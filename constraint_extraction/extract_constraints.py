import pandas as pd
import numpy as np
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
    
    print(f"Found tables: {table_names}")
    
    # Read from SQLite DB
    if os.path.exists(SQL_PATH):
        conn = sqlite3.connect(SQL_PATH)
        
        # Read each table
        tables_data = {}
        for table_name in table_names:
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                tables_data[table_name] = df
                print(f"Loaded table '{table_name}': {len(df)} rows")
            except Exception as e:
                print(f"Error loading table '{table_name}': {e}")
    else:
        print(f"SQLite file not found: {SQL_PATH}")
        return None

    # Calculate ranges
    table_range_cols = defaultdict(list)
    for table in table_names:
        for _, row in table_descriptions[table].iterrows():
            if isinstance(row['data_format'], str) and row['data_format'].lower() in ('integer', 'real'):
                table_range_cols[table].append(row['original_column_name'])
    
    table_range_stats = defaultdict(list)
    for table in table_names:
        for col in table_range_cols[table]:
            table_range_stats[table].append({
                'column': col,
                'max': tables_data[table][col].max(),
                'min': tables_data[table][col].min(),
                'mean': tables_data[table][col].mean()
            })
    
    for table in table_range_stats.keys():
        table_range_stats[table] = pd.DataFrame(table_range_stats[table])
            
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

    for table in table_categorical_stats.keys():
        table_categorical_stats[table] = pd.DataFrame(table_categorical_stats[table])


    # Calculate NOT NULL
    table_not_null_cols = defaultdict(list)
    for table in table_names:
        not_null_cols = [col for col in tables_data[table].columns 
                        if not tables_data[table][col].isnull().any()]
        table_not_null_cols[table] = not_null_cols

    def not_null_entries(table_name: str, cols: list[str]) -> list[dict]:
        return [{"not_null": [{"value": f"{table_name}__{col}"}]} for col in cols]

    entries = []
    for table in table_names:
        entries.extend(not_null_entries(table.upper(), table_not_null_cols[table]))

    not_null_output = {
        db_path: [
            entries
        ]
    }

    # Calculate dependencies
    table_dependencies = defaultdict(list)
    for table in table_names:
        dependencies = find_functional_dependencies(tables_data[table], table_name=table)
        table_dependencies[table] = dependencies

    return table_range_stats, table_categorical_stats, not_null_output, table_dependencies

def find_functional_dependencies(df, table_name=""):
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
    ranges_constraints, categorical_constraints, not_null_constraints, dependencies = extract("thrombosis_prediction")
    print(ranges_constraints)
    print(categorical_constraints)
    print(not_null_constraints)
    print(dependencies)

    
