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
    
def extract(db_path: str):
    db_name = os.path.basename(db_path)
    
    SQL_PATH = db_path + "/" + db_name + ".sqlite"
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

    # Format Constraints for VeriEQL
    all_constraints = []

    # Calculate ranges 
    table_range_cols = defaultdict(list)
    for table in table_names:
        for _, row in table_descriptions[table].iterrows():
            if isinstance(row['data_format'], str) and row['data_format'].lower() in ('integer', 'real'):
                table_range_cols[table].append(row['original_column_name'])

    table_range_stats = defaultdict(list)
    for table in table_names:
        for col in table_range_cols[table]:
            if col in tables_data[table].columns:
                table_range_stats[table].append({
                    'column': col,
                    'max': tables_data[table][col].max(),
                    'min': tables_data[table][col].min(),
                    'mean': tables_data[table][col].mean()
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
        dependencies = find_dependency(tables_data[table], table_name=table)
        table_dependencies[table] = dependencies

    # NOT NULL constraints
    for table in table_names:
        for col in table_not_null_cols[table]:
            normalized_col = col.upper().replace(' ', '_').replace('-', '_')
            all_constraints.append({
                "not_null": {"value": f"{table.upper()}__{normalized_col}"}
            })

   # BETWEEN constraints (for numeric ranges)
    for table in table_names:
        for stat in table_range_stats[table]:
            # Skip if min or max is NaN
            if pd.isna(stat['min']) or pd.isna(stat['max']):
                continue
            normalized_col = stat['column'].upper().replace(' ', '_').replace('-', '_')  
            all_constraints.append({
                "between": [
                    {"value": f"{table.upper()}__{normalized_col}"},  
                    stat['min'],
                    stat['max']
                ]
            })

    # IN constraints (for categorical)
    for table in table_names:
        for stat in table_categorical_stats[table]:
            normalized_col = stat['column'].upper().replace(' ', '_').replace('-', '_')  
            all_constraints.append({
                "in": [
                    {"value": f"{table.upper()}__{normalized_col}"}, 
                    stat['categories']
                ]
            })

    # Dependency constraints
    for table in table_names:
        for dep in table_dependencies[table]:
            det_col = dep['determinant'].upper().replace(' ', '_').replace('-', '_')
            dep_col = dep['dependent'].upper().replace(' ', '_').replace('-', '_')
            
            all_constraints.append({
                "dependency": {
                    "values": [
                        f"{table.upper()}__{det_col}",
                        f"{table.upper()}__{dep_col}"
                    ],
                    "mappings": dep['mappings']
                }
            })
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
                'mappings': dep_result['mappings']
            })
    
    return dependencies

def check_dependency(df, determinant_col, dependent_col):
    valid_df = df[[determinant_col, dependent_col]].dropna()
    
    if len(valid_df) == 0:
        return {'is_dependent': False, 'mappings': {}}
    
    # Group by determinant and check if dependent has only one unique value per group
    grouped = valid_df.groupby(determinant_col)[dependent_col]
    violations = (grouped.nunique() > 1).sum()
    
    if violations > 0:
        return {'is_dependent': False, 'mappings': {}}
    
    # Build mappings: determinant_value -> dependent_value
    mappings = {}
    for det_value, group in grouped:
        dep_value = group.iloc[0]  # Take first value (all are the same due to FD)
        # Convert to string for JSON serialization
        mappings[str(det_value)] = str(dep_value)
    
    return {
        'is_dependent': True,
        'mappings': mappings
    }

if __name__ == "__main__":
    schema, constraints = extract("thrombosis_prediction")
    #print("Schema:", schema)
    #print("Constraints:", constraints)

    
