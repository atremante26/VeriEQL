import sys
import os


import json
import csv
import traceback
import argparse
import re

def clean_up(generated_sql):

    def transform_backtick_content(match):
        """Transform the content inside backticks to a clean identifier."""
        content = match.group(1)  # Get content between backticks

        # Convert to uppercase
        content = content.upper()
        # Replace spaces with underscores
        content = content.replace(' ', '_')
        # Handle hyphens based on context
        content = re.sub(r'(\d+)-(\d+)', r'\1_\2', content)  # Numbers with hyphen -> underscore
        content = re.sub(r'([A-Z]+)-(\d+)', r'\1\2', content)  # Letters-number with hyphen -> remove hyphen
        # replace hyphen with underscore
        content = content.replace('-', '_')
        # Remove non-alphanumeric characters except underscores
        content = re.sub(r'[^A-Z0-9_]', '', content)
        # Clean up multiple consecutive underscores
        content = re.sub(r'_+', '_', content)


        # Remove leading/trailing underscores
        content = content.strip('_')

        return content

    # Find all backtick-quoted substrings and replace them
    # Pattern matches `anything inside backticks`
    pattern = r'`([^`]+)`'
    # Replace each backtick-quoted substring with its cleaned version
    generated_sql = re.sub(pattern, transform_backtick_content, generated_sql)

    # I also want to find all double quoted substrings and replace them with their cleaned version
    pattern = r'"([^"]+)"'
    generated_sql = re.sub(pattern, transform_backtick_content, generated_sql)

    return generated_sql

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('prediction_path', type=str, help='Path to prediction JSON file', default='./predictions_spider2/omni_portfolio.json')
    parser.add_argument('--index', type=int, required=True, help='Index to process', default=4)
    parser.add_argument('--bound', type=int, required=True, help='Bound size for verification', default=1)
    parser.add_argument('--vanilla', action='store_true', help='Use vanilla VeriEQL')

    args = parser.parse_args()

    # Get the base directory from the script location
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, base_dir)
    if args.vanilla:
        from VeriEQL_vanilla.verieql import verify_sql_equivalence
        from VeriEQL_vanilla.constants import DIALECT
    else:
        from verieql import verify_sql_equivalence
        from constants import DIALECT

    index = args.index
    bound_size = args.bound

    # Paths for Spider2 data
    GOLD_QUERIES_PATH = os.path.join(base_dir, "predictions_spider2", "gold_queries.json")
    INDEX_TO_DATABASE_PATH = os.path.join(base_dir, "Spider2_schemas", "index_to_database.json")
    TABLE_TO_COLUMNS_PATH = os.path.join(base_dir, "Spider2_schemas", "table_to_columns.json")

    print(f"Running index {index} with bound {bound_size}")

    csv_path = "./out.csv"
    counter_example_path = "./counterexample.txt"
    csv_headers = ['bound_size', 'question_id', 'equivalent', 'error', 'time_cost', 'generated_sql', 'gold_sql']

    with open(csv_path, 'w', newline='') as csvfile:

        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()
                    
        try:
            # Load gold queries
            with open(GOLD_QUERIES_PATH, 'r') as f:
                gold_queries = json.load(f)
            
            if str(index) not in gold_queries:
                raise ValueError(f"Index {index} not found in gold_queries.json")
            
            gold_sql = gold_queries[str(index)]
            gold_sql = gold_sql.upper()
            print(f"GOLD_SQL BEFORE: {gold_sql}")
            gold_sql = clean_up(gold_sql)
            print(f"GOLD_SQL AFTER: {gold_sql}")

            # Load index to database mapping
            with open(INDEX_TO_DATABASE_PATH, 'r') as f:
                index_to_database = json.load(f)
            
            if str(index) not in index_to_database:
                raise ValueError(f"Index {index} not found in index_to_database.json")
            
            database_id = index_to_database[str(index)]
            print(f"Database: {database_id}")

            # Get the generated SQL from prediction file
            with open(args.prediction_path, 'r') as f:
                output_dic = json.load(f)
            
            if str(index) not in output_dic:
                raise ValueError(f"Index {index} not found in prediction file {args.prediction_path}")
            
            generated_sql = output_dic[str(index)]
            # Handle cases where SQL might be split by tab or newline
            stopper = '\t'
            if stopper in generated_sql:
                generated_sql = generated_sql.split(stopper)[0]
            generated_sql = ' '.join(generated_sql.split())
            generated_sql = generated_sql.upper()
            print(f"GENERATED_SQL BEFORE: {generated_sql}")
            generated_sql = clean_up(generated_sql)
            print(f"GENERATED_SQL AFTER: {generated_sql}")

            # Get the schema
            with open(TABLE_TO_COLUMNS_PATH, 'r') as f:
                schema = json.load(f)
            
            if database_id not in schema:
                raise ValueError(f"Database {database_id} not found in table_to_columns.json")
            
            # Handle constraints - use empty list if constraints file doesn't exist
            constraints = []
            constraints_path = os.path.join(base_dir, "Spider2_schemas", "table_constraints.json")
            if os.path.exists(constraints_path):
                with open(constraints_path, 'r') as f:
                    constraints_data = json.load(f)
                    if database_id in constraints_data:
                        constraints = constraints_data[database_id]
                        if isinstance(constraints, list) and len(constraints) > 0:
                            constraints = constraints[0]
                        else:
                            constraints = []
            else:
                print(f"Warning: Constraints file not found at {constraints_path}, using empty constraints")

            config = {'generate_code': True, 
                      'timer': True, 
                      'show_counterexample': True, 
                      'dialect': DIALECT.MYSQL,
                      "all_null_is_deleted": True, 
                      }
            if not args.vanilla:
                DATE_KEYS = ["STRFTIME"]
                config["encode_date"] = config.get("encode_date", False) or any(
                    any(map(lambda query: key in str.upper(query), [generated_sql, gold_sql])) for key in DATE_KEYS)
                # encode_string = True: must encode strings as Z3 builtin strings;
                # encode_string = False: only follow this encoding if queries involve SUBSTR, LIKE
                # since date involves arithmetic operations, once encode_date = True, encode_string must be True.
                STRING_KEYS = [" LIKE ", "SUBSTR"]
                config["encode_string"] = config.get("encode_string", False) or any(
                    any(map(lambda query: key in str.upper(query), [generated_sql, gold_sql])) for key in STRING_KEYS) or config["encode_date"]

                verification_result = verify_sql_equivalence(generated_sql, gold_sql, schema[database_id], bound_size, constraints, **config)
            else:
                verification_result = verify_sql_equivalence(generated_sql, gold_sql, schema[database_id], bound_size, constraints, **config)

            csv_row = {
                'bound_size': bound_size,
                'question_id': index,
                'equivalent': verification_result['equivalent'],
                'error': '',
                'time_cost': verification_result['time_cost'] if verification_result['time_cost'] else '',
                'generated_sql': generated_sql,
                'gold_sql': gold_sql
            }

            if verification_result['counterexample'] is not None:
                ce = verification_result['counterexample']
                with open(counter_example_path, 'w') as f:
                    f.write(ce)
                
            writer.writerow(csv_row)
            csvfile.flush() 
                        
        except Exception as e:
            traceback.print_exc()

            csv_row = {
                'bound_size': bound_size,
                'question_id': index,
                'equivalent': 'ERROR',
                'error': f"{type(e).__name__}: {str(e)}",
                'time_cost': '',
                'generated_sql': generated_sql if 'generated_sql' in locals() else '',
                'gold_sql': gold_sql if 'gold_sql' in locals() else ''
            }
            
            writer.writerow(csv_row)
            csvfile.flush()
