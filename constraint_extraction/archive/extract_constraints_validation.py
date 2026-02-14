import pandas as pd
import json
import os
import sqlite3
import numpy as np
from collections import defaultdict
from itertools import combinations

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def validate(constraint, df, schema, table_name):
    """
    Validate if a constraint holds true on the given dataframe (dev set).
    """
    try:
        # NOT NULL validation
        if "not_null" in constraint:
            col_name = constraint["not_null"]["value"].split("__")[1]
            # Map schema column name back to data column name
            if col_name not in df.columns:
                # Try with space instead of underscore
                col_name_with_space = col_name.replace('_', ' ')
                if col_name_with_space in df.columns:
                    col_name = col_name_with_space
                else:
                    return False
            
            # Check if column has any null values
            return not df[col_name].isnull().any()
        
        # BETWEEN validation
        elif "between" in constraint:
            col_name = constraint["between"][0]["value"].split("__")[1]
            min_val = constraint["between"][1] # Min from train
            max_val = constraint["between"][2] # Max from train
            
            # Map schema column name back to data column name
            if col_name not in df.columns:
                col_name_with_space = col_name.replace('_', ' ')
                if col_name_with_space in df.columns:
                    col_name = col_name_with_space
                else:
                    return False
            
            # Convert to numeric and check range
            numeric_col = pd.to_numeric(df[col_name], errors='coerce').dropna()
            if len(numeric_col) == 0:
                return False
            
            # Check if all values are within the range
            return (numeric_col >= min_val).all() and (numeric_col <= max_val).all()
        
        # IN validation
        elif "in" in constraint:
            col_name = constraint["in"][0]["value"].split("__")[1]
            allowed_values = set(constraint["in"][1]) # Categories from train
            
            # Map schema column name back to data column name
            if col_name not in df.columns:
                col_name_with_space = col_name.replace('_', ' ')
                if col_name_with_space in df.columns:
                    col_name = col_name_with_space
                else:
                    return False
            
            # Get column type from schema
            table_upper = table_name.upper()
            schema_col = col_name.replace(' ', '_').upper()
            
            if table_upper in schema and schema_col in schema[table_upper]:
                col_type = schema[table_upper][schema_col]
                
                # Convert dataframe values to match type
                actual_values = df[col_name].dropna()
                try:
                    if col_type == 'INTEGER':
                        actual_values = actual_values.astype(int)
                    elif col_type == 'REAL':
                        actual_values = actual_values.astype(float)
                    else:
                        actual_values = actual_values.astype(str)
                except (ValueError, TypeError):
                    return False
                
                # Check if all values are in allowed set
                return set(actual_values.unique()).issubset(allowed_values)
            
            return False
        
        # DEPENDENCY validation
        elif "dependency" in constraint:
            det_col = constraint["dependency"]["values"][0].split("__")[1] # Determinant
            dep_col = constraint["dependency"]["values"][1].split("__")[1] # Dependent
            
            # Map schema column names back to data column names
            if det_col not in df.columns:
                det_col_with_space = det_col.replace('_', ' ')
                if det_col_with_space in df.columns:
                    det_col = det_col_with_space
                else:
                    return False
            
            if dep_col not in df.columns:
                dep_col_with_space = dep_col.replace('_', ' ')
                if dep_col_with_space in df.columns:
                    dep_col = dep_col_with_space
                else:
                    return False
            
            # Check functional dependency
            valid_df = df[[det_col, dep_col]].dropna()
            if len(valid_df) == 0:
                return False
            
            # Group by determinant and check if dependent has only one unique value per group
            grouped = valid_df.groupby(det_col)[dep_col]
            violations = (grouped.nunique() > 1).sum()
            
            return violations == 0
        
        # Skip validation for existing constraints (primary/foreign keys)
        else:
            return True
            
    except Exception as e:
        # If validation fails for any reason, reject the constraint
        print(f"    Validation error for constraint {constraint}: {e}")
        return False
    
def extract(db_path: str, validate_constraints=False):
    """
    Extract constraints from a database.
    """
    db_name = os.path.basename(db_path)
    
    SQL_PATH = db_path + "/" + db_name + "_train.sqlite"
    DEV_SQL_PATH = db_path + "/" + db_name + "_dev.sqlite"
    DESCRIPTION_PATH = db_path + "/database_description"
    DEV_CONSTRAINTS_PATH = "../BIRD_schemas/dev_constraints.json" 

   # Extract table names
    table_names = []
    table_descriptions = {}
    if os.path.exists(DESCRIPTION_PATH):
        for filename in os.listdir(DESCRIPTION_PATH):
            if filename.endswith('.csv'):
                table_name = filename[:-4]
                
                try:
                    # Try UTF-8 first
                    table = pd.read_csv(f"{DESCRIPTION_PATH}/{filename}", 
                                    on_bad_lines='skip',
                                    encoding='utf-8')
                    table_names.append(table_name)
                    table_descriptions[table_name] = table
                except UnicodeDecodeError:
                    try:
                        # Try latin-1 as fallback
                        table = pd.read_csv(f"{DESCRIPTION_PATH}/{filename}", 
                                        on_bad_lines='skip',
                                        encoding='latin-1')
                        table_names.append(table_name)
                        table_descriptions[table_name] = table
                    except Exception as e:
                        print(f"Warning: Could not read description for table '{table_name}': {e}")
                        table_names.append(table_name)
                except Exception as e:
                    print(f"Warning: Could not read description for table '{table_name}': {e}")
                    table_names.append(table_name)

    # Read from SQLite DB (TRAIN DATA)
    if os.path.exists(SQL_PATH):
        conn = sqlite3.connect(SQL_PATH)
        
        tables_data = {}
        for table_name in table_names:
            try:
                # Quote table name to handle reserved words
                df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
                tables_data[table_name] = df
            except Exception as e:
                print(f"Error loading table '{table_name}': {e}")
                continue
        conn.close()
    else:
        print(f"SQLite file not found: {SQL_PATH}")
        return None
    
    # Read DEV data if validation is enabled
    dev_tables_data = {}
    if validate_constraints:
        if os.path.exists(DEV_SQL_PATH):
            dev_conn = sqlite3.connect(DEV_SQL_PATH)
            
            for table_name in table_names:
                try:
                    df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', dev_conn)
                    dev_tables_data[table_name] = df
                except Exception as e:
                    print(f"Error loading dev table '{table_name}': {e}")
                    continue
            dev_conn.close()
        else:
            print(f"Warning: Dev SQLite file not found: {DEV_SQL_PATH}, skipping validation")
            validate_constraints = False
    
    # Load existing schema from table_to_columns.json instead of building our own
    SCHEMA_PATH = "../BIRD_schemas/table_to_columns.json"
    if os.path.exists(SCHEMA_PATH):
        with open(SCHEMA_PATH, 'r') as f:
            all_schemas = json.load(f)
        schema = all_schemas.get(db_name, {})
    else:
        print(f"Warning: Schema file not found at {SCHEMA_PATH}")
        schema = {}

    # Load existing constraints from dev_constraints.json
    existing_constraints = []
    if os.path.exists(DEV_CONSTRAINTS_PATH):
        with open(DEV_CONSTRAINTS_PATH, 'r') as f:
            dev_constraints = json.load(f)
        
        # Get constraints for this specific database
        if db_name in dev_constraints:
            existing_constraints = dev_constraints[db_name][0]  # Get the constraint list
    
    # Helper function to map data column names to schema column names
    def get_schema_col_name(table_name, data_col_name):
        """Map a data column name to its schema column name"""
        table_upper = table_name.upper()
        if table_upper not in schema:
            return None
        
        # Try exact match first
        data_col_upper = data_col_name.upper()
        if data_col_upper in schema[table_upper]:
            return data_col_upper
        
        # Try with space normalization
        normalized = data_col_upper.replace(' ', '_')
        if normalized in schema[table_upper]:
            return normalized
        
        # If still no match, return None
        return None
            
    # Format Constraints for VeriEQL
    all_constraints = []
    
    # Add existing constraints (primary/foreign keys with TABLE__ prefix)
    all_constraints.extend(existing_constraints)

    # Track validation statistics
    validation_stats = {
        'not_null': {'extracted': 0, 'validated': 0},
        'between': {'extracted': 0, 'validated': 0},
        'in': {'extracted': 0, 'validated': 0},
        'dependency': {'extracted': 0, 'validated': 0}
    }
    # ============================================================================================================================
    # Calculate ranges - USE ACTUAL COLUMNS FROM TABLES_DATA
    table_range_cols = defaultdict(list)
    for table in table_names:
        if table not in tables_data:
            continue
        
        # Get numeric columns directly from the actual data
        for col in tables_data[table].columns:
            numeric_col = pd.to_numeric(tables_data[table][col], errors='coerce')
            if len(numeric_col.dropna()) > 1:
                table_range_cols[table].append(col)

    table_range_stats = defaultdict(list)
    for table in table_names:
        for col in table_range_cols[table]:
            numeric_col = pd.to_numeric(tables_data[table][col], errors='coerce')
            
            if len(numeric_col.dropna()) > 1:
                min_val = numeric_col.min()
                max_val = numeric_col.max()
                
                if pd.notna(min_val) and pd.notna(max_val):
                    table_range_stats[table].append({
                        'column': col,
                        'max': max_val,
                        'min': min_val,
                        'mean': numeric_col.mean()
                    })

    # Calculate categorical - USE ACTUAL COLUMNS FROM TABLES_DATA
    table_categorical_cols = defaultdict(list)
    for table in table_names:
        if table not in tables_data:
            continue
        
        # Get text/categorical columns directly from the actual data
        for col in tables_data[table].columns:
            # If column is not numeric and has reasonable number of unique values
            if tables_data[table][col].dtype == 'object' or tables_data[table][col].dtype == 'string':
                unique_count = tables_data[table][col].nunique()
                if 1 < unique_count <= 50:  # Reasonable threshold for categorical
                    table_categorical_cols[table].append(col)

    table_categorical_stats = defaultdict(list)
    for table in table_names:
        for col in table_categorical_cols[table]:
            unique_vals = tables_data[table][col].dropna().unique()
            table_categorical_stats[table].append({
                'column': col,
                'categories': unique_vals.tolist()
            })

    # Calculate NOT NULL
    table_not_null_cols = defaultdict(list)
    for table in table_names:
        not_null_cols = [col for col in tables_data[table].columns 
                        if not tables_data[table][col].isnull().any()]
        table_not_null_cols[table] = not_null_cols

    # Calculate Dependencies
    table_dependencies = defaultdict(list)
    for table in table_names:
        dependencies = find_dependency(tables_data[table], table_name=table)
        table_dependencies[table] = dependencies
    # ===========================================================================================================================
    # NOT NULL constraints - USE SCHEMA COLUMN NAMES
    for table in table_names:
        for col in table_not_null_cols[table]:
            schema_col = get_schema_col_name(table, col)
            if schema_col:
                constraint = {
                    "not_null": {"value": f"{table.upper()}__{schema_col}"}
                }
                validation_stats['not_null']['extracted'] += 1
                
                # Validate if enabled
                if validate_constraints and table in dev_tables_data:
                    if validate(constraint, dev_tables_data[table], schema, table):
                        all_constraints.append(constraint)
                        validation_stats['not_null']['validated'] += 1
                else:
                    all_constraints.append(constraint)

    # BETWEEN constraints - USE SCHEMA COLUMN NAMES
    for table in table_names:
        for stat in table_range_stats[table]:
            schema_col = get_schema_col_name(table, stat['column'])
            if schema_col and pd.notna(stat['min']) and pd.notna(stat['max']):
                # Check if column is actually numeric in the schema
                table_upper = table.upper()
                if table_upper in schema and schema_col in schema[table_upper]:
                    col_type = schema[table_upper][schema_col]
                    # Only add BETWEEN for numeric types
                    if col_type not in ['INTEGER', 'REAL']:
                        continue
                
                # Strategy 5: Only keep BETWEEN for useful constraints
                is_id_column = 'ID' in schema_col.upper()
                range_span = stat['max'] - stat['min']
                is_wide_range = range_span > 100
                
                # Skip if it's not an ID column and doesn't have a wide range
                if not (is_id_column or is_wide_range):
                    continue
                
                constraint = {
                    "between": [
                        {"value": f"{table.upper()}__{schema_col}"},  
                        stat['min'],
                        stat['max']
                    ]
                }
                validation_stats['between']['extracted'] += 1
                
                # Validate if enabled
                if validate_constraints and table in dev_tables_data:
                    if validate(constraint, dev_tables_data[table], schema, table):
                        all_constraints.append(constraint)
                        validation_stats['between']['validated'] += 1
                else:
                    all_constraints.append(constraint)

    # IN constraints - USE SCHEMA COLUMN NAMES, ENSURE TYPE CONSISTENCY
    for table in table_names:
        for stat in table_categorical_stats[table]:
            filtered_categories = [cat for cat in stat['categories'] if cat != ""]
            n_filtered_categories = len(filtered_categories)
            
            if n_filtered_categories <= 5 and n_filtered_categories > 0:
                schema_col = get_schema_col_name(table, stat['column'])
                if schema_col:
                    # Check schema type and ensure all values match
                    table_upper = table.upper()
                    if table_upper in schema and schema_col in schema[table_upper]:
                        col_type = schema[table_upper][schema_col]
                        
                        # Convert all values to match schema type
                        try:
                            if col_type == 'INTEGER':
                                filtered_categories = [int(cat) for cat in filtered_categories]
                            elif col_type == 'REAL':
                                filtered_categories = [float(cat) for cat in filtered_categories]
                            else:  # VARCHAR/TEXT/DATE
                                filtered_categories = [str(cat) for cat in filtered_categories]
                        except (ValueError, TypeError):
                            # Skip this constraint if type conversion fails
                            continue
                        
                        constraint = {
                            "in": [
                                {"value": f"{table.upper()}__{schema_col}"},
                                filtered_categories
                            ]
                        }
                        validation_stats['in']['extracted'] += 1
                        
                        # Validate if enabled
                        if validate_constraints and table in dev_tables_data:
                            if validate(constraint, dev_tables_data[table], schema, table):
                                all_constraints.append(constraint)
                                validation_stats['in']['validated'] += 1
                        else:
                            all_constraints.append(constraint)

    # DEPENDENCY constraints - USE SCHEMA COLUMN NAMES
    for table in table_names:
        for dep in table_dependencies[table]:
            det_schema_col = get_schema_col_name(table, dep['determinant'])
            dep_schema_col = get_schema_col_name(table, dep['dependent'])
            
            if det_schema_col and dep_schema_col:
                constraint = {
                    "dependency": {
                        "values": [
                            f"{table.upper()}__{det_schema_col}",
                            f"{table.upper()}__{dep_schema_col}"
                        ]
                    }
                }
                validation_stats['dependency']['extracted'] += 1
                
                # Validate if enabled
                if validate_constraints and table in dev_tables_data:
                    if validate(constraint, dev_tables_data[table], schema, table):
                        all_constraints.append(constraint)
                        validation_stats['dependency']['validated'] += 1
                else:
                    all_constraints.append(constraint)
    
    # Format for VeriEQL
    constraints_output = {
        db_name: [
            all_constraints
        ]
    }

    # Create output directory
    output_dir = os.path.join(os.path.dirname(db_path), 'constraint_results')
    os.makedirs(output_dir, exist_ok=True)

    # Save to schema JSON
    schema_output = {db_name: schema}
    with open(os.path.join(output_dir, f'{db_name}_schema.json'), 'w') as f:
        json.dump(schema_output, f, indent=2, cls=NumpyEncoder)

    # Save constraints to JSON
    with open(os.path.join(output_dir, f'{db_name}_constraints.json'), 'w') as f:
        json.dump(constraints_output, f, indent=2, cls=NumpyEncoder)
    

    print(f"\nSummary for {db_name}:")
    print(f"  Tables with descriptions: {len(table_descriptions)}/{len(table_names)}")
    if len(table_descriptions) < len(table_names):
        missing = set(table_names) - set(table_descriptions.keys())
        print(f"  Tables without descriptions: {missing}")
    print(f"  Total constraints generated: {len(all_constraints)}")
    
    if validate_constraints:
        print(f"\n  Validation Results:")
        for constraint_type, stats in validation_stats.items():
            if stats['extracted'] > 0:
                pct = (stats['validated'] / stats['extracted']) * 100
                print(f"    {constraint_type}: {stats['validated']}/{stats['extracted']} ({pct:.1f}%)")

    return schema, constraints_output


def find_dependency(df, table_name=""):
    dependencies = []
    columns = df.columns.tolist()
    
    for col_a, col_b in combinations(columns, 2):
        if df[col_a].equals(df[col_b]):
            continue
        
        # Check if col_a determines col_b
        dep_result = check_dependency(df, col_a, col_b)
        if dep_result['is_dependent']:
            dependencies.append({
                'table': table_name,
                'determinant': col_a,
                'dependent': col_b,
            })
    
    return dependencies

def check_dependency(df, determinant_col, dependent_col):
    valid_df = df[[determinant_col, dependent_col]].dropna()
    
    if len(valid_df) == 0:
        return {'is_dependent': False}
    
    # Group by determinant and check if dependent has only one unique value per group
    grouped = valid_df.groupby(determinant_col)[dependent_col]
    violations = (grouped.nunique() > 1).sum()
    
    if violations > 0:
        return {'is_dependent': False}
    
    return {
        'is_dependent': True
    }

if __name__ == "__main__":
    # Define all database paths
    database_paths = {
        "thrombosis_prediction": "BIRD_dev_split/thrombosis_prediction",
        "california_schools": "BIRD_dev_split/california_schools",
        "debit_card_specializing": "BIRD_dev_split/debit_card_specializing",
        "financial": "BIRD_dev_split/financial",
        "formula_1": "BIRD_dev_split/formula_1",
        "card_games": "BIRD_dev_split/card_games",
        "european_football_2": "BIRD_dev_split/european_football_2",
        "toxicology": "BIRD_dev_split/toxicology",
        "student_club": "BIRD_dev_split/student_club",
        "superhero": "BIRD_dev_split/superhero",
        "codebase_community": "BIRD_dev_split/codebase_community"
    }
    
    # Collect all constraints
    all_constraints = {}
    
    for db_name, db_path in database_paths.items():
        print(f"\n{'='*60}")
        print(f"Processing database: {db_name}")
        print(f"{'='*60}")
        
        try:
            # Extract constraints from train set and validate on dev set
            _, constraints_output = extract(
                db_path, 
                validate_constraints=True
            )
            
            # Add to master dictionary
            all_constraints.update(constraints_output)
            
            print(f"Successfully processed {db_name}")
        except Exception as e:
            print(f"Error processing {db_name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Save all constraints to a single JSON file
    output_path = "constraint_results/all_constraints_validated.json"
    os.makedirs("constraint_results", exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(all_constraints, f, indent=2, cls=NumpyEncoder)
    
    print(f"\n{'='*60}")
    print(f"Saved all validated constraints to: {output_path}")
    print(f"Total databases processed: {len(all_constraints)}")
    print(f"{'='*60}")