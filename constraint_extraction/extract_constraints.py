import pandas as pd
import numpy as np
import os
import sqlite3
from collections import defaultdict

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
    
    for table, stats in table_range_stats.items():
        table_range_stats[table] = pd.DataFrame(stats)
            
    # Calculate categorical
    table_categorical_cols = defaultdict(list)
    for table in table_names:
        for _, row in table_descriptions[table].iterrows():
            if isinstance(row['data_format'], str) and row['data_format'].lower() in ('text'):
                table_range_cols[table].append(row['original_column_name'])

    table_categorical_stats = defaultdict(list)
    for table in table_names:
        for col in table_range_cols[table]:
            table_categorical_stats[table].append({
                'column': col,
                'categories': tables_data[table][col].unique(),
                'n_categories': tables_data[table][col].nunique()
            })

    for table, stats in table_categorical_stats.items():
        table_range_stats[table] = pd.DataFrame(stats)


    # Calculate NOT NULL
    

if __name__ == "__main__":
    extract("thrombosis_prediction")