import pandas as pd
import json
import os
import sqlite3
from collections import defaultdict
from itertools import combinations

def extract(db_path: str):
    SQL_PATH = db_path + "/" + db_path + ".sqlite"
    DESCRIPTION_PATH = db_path + "/database_description"

    # Extract table names
    table_names = []
    table_descriptions = {}
    if os.path.exists(DESCRIPTION_PATH):
        for filename in os.listdir(DESCRIPTION_PATH):
            if filename.endswith('.csv'):
                # Extract table name 
                table_name = filename[:-4]
                table_names.append(table_name)

                # Append table to table descriptions
                table = pd.read_csv(f"{DESCRIPTION_PATH}/{filename}")
                table_descriptions[table_name] = table

    # Read from SQLite DB
    if os.path.exists(SQL_PATH):
        conn = sqlite3.connect(SQL_PATH)
        
        # Read each table
        tables_data = {}
        for table_name in table_names:
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                tables_data[table_name] = df
            except Exception as e:
                print(f"Error loading table '{table_name}': {e}")
    else:
        print(f"SQLite file not found: {SQL_PATH}")
        return None
    
    # Build schema
    schema = {}
    for table_name in table_names:
        schema[table_name.upper()] = {}
        
        # Get column info
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        
        for col_info in columns_info:
            col_name = col_info[1]  # Column name
            col_type = col_info[2].upper()  # Column type
            
            # Normalize column name
            normalized_col_name = col_name.upper().replace(' ', '_')
            
            # Map SQLite types to VeriEQL types
            if col_type in ('INTEGER', 'INT'):
                schema[table_name.upper()][normalized_col_name] = 'INTEGER'
            elif col_type in ('REAL', 'FLOAT', 'DOUBLE'):
                schema[table_name.upper()][normalized_col_name] = 'REAL'
            elif col_type in ('TEXT', 'VARCHAR', 'CHAR'):
                schema[table_name.upper()][normalized_col_name] = 'VARCHAR'
            elif col_type == 'DATE':
                schema[table_name.upper()][normalized_col_name] = 'DATE'
            else:
                schema[table_name.upper()][normalized_col_name] = 'VARCHAR'

    # Calculate ranges
    table_range_cols = defaultdict(list)
    for table in table_names:
        for _, row in table_descriptions[table].iterrows():
            if isinstance(row['data_format'], str) and row['data_format'].lower() in ('integer', 'real'):
                table_range_cols[table].append(row['original_column_name'])

    table_range_stats = defaultdict(list)
    for table in table_names:
        for stat in table_range_stats[table]:
            all_constraints.append({
                "between": [
                    [{"value": f"{table.upper()}__{stat['column']}"}],
                    float(stat['min']) if pd.notna(stat['min']) else None,  # Convert to Python float
                    float(stat['max']) if pd.notna(stat['max']) else None   # Convert to Python float
                ]
            })

    # Calculate categorical
    table_categorical_cols = defaultdict(list)
    for table in table_names:
        for _, row in table_descriptions[table].iterrows():
            if isinstance(row['data_format'], str) and row['data_format'].lower() == 'text':
                table_categorical_cols[table].append(row['original_column_name'])

    table_categorical_stats = defaultdict(list)
    for table in table_names:
        for col in table_categorical_cols[table]:
            if col in tables_data[table].columns:
                unique_vals = tables_data[table][col].dropna().unique()
                table_categorical_stats[table].append({
                    'column': col,
                    'categories': unique_vals.tolist(),  
                    'n_categories': tables_data[table][col].nunique()
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
        dependencies = find_dependencies(tables_data[table], table_name=table)
        table_dependencies[table] = dependencies

    # TODO: NEED TO IMPLEMENT DEPENDENCIES CONSTRAINTS

    # Format Constraints for VeriEQL
    all_constraints = []

    # NOT NULL constraints
    for table in table_names:
        for col in table_not_null_cols[table]:
            all_constraints.append({
                "not_null": [{"value": f"{table.upper()}__{col}"}]
            })

    # BETWEEN constraints (for numeric ranges)
    for table in table_names:
        for stat in table_range_stats[table]:
            all_constraints.append({
                "between": [
                    [{"value": f"{table.upper()}__{stat['column']}"}],
                    stat['min'],
                    stat['max']
                ]
            })

    # IN constraints (for categorical)
    for table in table_names:
        for stat in table_categorical_stats[table]:
            all_constraints.append({
                "in": [
                    [{"value": f"{table.upper()}__{stat['column']}"}],
                    stat['categories']
                ]
            })

    # Format for VeriEQL
    constraints_output = {
        db_path: [
            all_constraints
        ]
    }

    # Save to schema JSON
    schema_output = {db_path: schema}
    with open(f'constraint_results/{db_path}_schema.json', 'w') as f:
        json.dump(schema_output, f, indent=2)
    
    # Save constraints to JSON
    with open(f'constraint_results/{db_path}_constraints.json', 'w') as f:
        json.dump(constraints_output, f, indent=2)

    return schema, constraints_output


def find_dependencies(df, table_name=""):
    dependencies = []
    columns = df.columns.tolist()
        
    # Check each pair of columns
    for col_a, col_b in combinations(columns, 2):
        # Skip if columns are identical
        if df[col_a].equals(df[col_b]):
            continue
            
        # Check if col_a determines col_b
        dep_a_to_b = check_dependency(df, col_a, col_b)
        if dep_a_to_b['is_dependent']:
            dependencies.append({
                'table': table_name,
                'determinant': col_a,
                'dependent': col_b,
                'confidence': dep_a_to_b['confidence'],
                'violations': dep_a_to_b['violations']
            })
            
        # Check if col_b determines col_a
        dep_b_to_a = check_dependency(df, col_b, col_a)
        if dep_b_to_a['is_dependent']:
            dependencies.append({
                'table': table_name,
                'determinant': col_b,
                'dependent': col_a,
                'confidence': dep_b_to_a['confidence'],
                'violations': dep_b_to_a['violations']
            })
        
    return dependencies

def check_dependency(df, determinant_col, dependent_col):
    valid_df = df[[determinant_col, dependent_col]].dropna()
        
    if len(valid_df) == 0:
        return {'is_dependent': False, 'confidence': 0, 'violations': 0}
        
    grouped = valid_df.groupby(determinant_col)[dependent_col].nunique()
    violations = (grouped > 1).sum()
    total_groups = len(grouped)
    confidence = ((total_groups - violations) / total_groups) * 100 if total_groups > 0 else 0
    is_dependent = (violations == 0 and confidence == 100.0)
        
    return {
        'is_dependent': is_dependent,
        'confidence': confidence,
        'violations': int(violations)
    }

if __name__ == "__main__":
    schema, constraints = extract("thrombosis_prediction")
    #print("Schema:", schema)
    #print("Constraints:", constraints)

    
