from collections import defaultdict
import json
import re

def clean_up_column_name(name):
    # Convert to uppercase
    content = name.upper()
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

def column_type_mapping(column_type):
    mapping = {
        "text": "VARCHAR",
        "integer": "INTEGER",
        "real": "REAL",
        "date": "DATE",
        "datetime": "DATE",
    }
    return mapping[column_type]

def main():
    # Paths to the JSON files
    dev_tables_path = "../BIRD_schemas/dev_tables.json"

    # Load dev_tables.json
    with open(dev_tables_path, "r") as f:
        dev_tables = json.load(f)

    table = {}
    constraints = {}
    # Build the mapping
    mapping_orig_to_clean = {}
    mapping_clean_to_orig = {}
    for db in dev_tables:
        db_id = db["db_id"]
        mapping_orig_to_clean[db_id] = {}
        mapping_clean_to_orig[db_id] = {}
        # Get table names and columns
        table_names = db["table_names_original"]
        # Assert that the table names only contains english letters
        for t in table_names:
            assert re.match(r'^[A-Za-z0-9_]+$', t)

        column_names = db["column_names_original"]
        column_types = db["column_types"]
        primary_keys = db["primary_keys"]
        foreign_keys = db["foreign_keys"]
        # column_names is a flat list, but we want per-table mapping
        # Build a per-table column list
        table_to_columns = defaultdict(dict)
        constraint = []
        idx = 0
        for index, column_name in column_names:
            if index >= 0:
                idx += 1
                column_name_clean = clean_up_column_name(column_name)
                table_to_columns[table_names[index].upper()][column_name_clean] = column_type_mapping(column_types[idx])

                print("Rewriting:", column_name, "->", column_name_clean)

                mapping_orig_to_clean[db_id][column_name] = (column_name_clean)
                mapping_clean_to_orig[db_id][column_name_clean] = (column_name)

        for pk in primary_keys:
            # if pk is list
            if isinstance(pk, int):
                pk = [pk]
            for p in pk:
                table_name = table_names[column_names[p][0]].upper()
                column_name = column_names[p][1]
                column_name_clean = mapping_orig_to_clean[db_id][column_name]
                constraint.append({"primary": [{"value": f"{table_name}__{column_name_clean}"}]})

        for k1, k2 in foreign_keys:
            table1 = table_names[column_names[k1][0]].upper()
            col1 = column_names[k1][1]
            col1_clean = mapping_orig_to_clean[db_id][col1]
            table2 = table_names[column_names[k2][0]].upper()
            col2 = column_names[k2][1]
            col2_clean = mapping_orig_to_clean[db_id][col2]
            constraint.append({"foreign": [{"value": f"{table1}__{col1_clean}"}, {"value": f"{table2}__{col2_clean}"}]})

        table[db_id] = table_to_columns
        constraints[db_id] = [constraint]
    
    # store table to a json file
    with open("table_to_columns.json", "w") as f:
        json.dump(table, f, indent=4)

    with open("table_constraints.json", "w") as f:
        json.dump(constraints, f, indent=4)

    with open("column_name_mapping.json", "w") as f:
        json.dump({
            "orig_to_clean": mapping_orig_to_clean,
            "clean_to_orig": mapping_clean_to_orig
        }, f, indent=4)

    # Compare verieql_table_definitions with table
    #for db_id in verieql_table_definitions:
    #    for table_name in verieql_table_definitions[db_id]:
    #         if table_name not in table[db_id]:
    #             print(f"Table {table_name} in verieql but not in processed table for db {db_id}")
    #         else:
    #             verieql_columns = verieql_table_definitions[db_id][table_name]
    #             processed_columns = table[db_id][table_name]
    #             for col in verieql_columns:
    #                 if col not in processed_columns:
    #                     print(f"Column {col} in verieql but not in processed table {table_name} for db {db_id}")
    #             for col in processed_columns:
    #                 if col not in verieql_columns:
    #                     print(f"Column {col} in processed table but not in verieql table {table_name} for db {db_id}")

if __name__ == "__main__":
    main()