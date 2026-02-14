#!/usr/bin/env python3

import sqlite3
import os
import argparse
import random
from pathlib import Path


def get_table_names(db_path):
    """Get all user-created table names in the database (exclude internal tables)."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def get_table_schema(db_path, table_name):
    """Get the CREATE TABLE statement for a table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
    schema = cursor.fetchone()[0]
    conn.close()
    return schema


def get_all_rows(db_path, table_name):
    """Get all rows from a table."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM "{table_name}"')
    rows = cursor.fetchall()
    conn.close()
    return rows


def split_database(input_db_path, output_dir, train_ratio=0.8, random_seed=42, overwrite=False):
    """
    Split a database into train and dev sets.
    """
    random.seed(random_seed)
    
    # Get database name and parent directory
    input_path = Path(input_db_path)
    db_name = input_path.stem
    parent_dir = input_path.parent
    
    # Create output folder structure: output_dir/db_name/
    output_db_dir = os.path.join(output_dir, db_name)
    
    # Check if output already exists
    if os.path.exists(output_db_dir) and not overwrite:
        print(f"Skipping {db_name} (already exists, use --overwrite to regenerate)\n")
        return
    
    # If overwriting, remove old database files
    if overwrite and os.path.exists(output_db_dir):
        train_db_path_old = os.path.join(output_db_dir, f"{db_name}_train.sqlite")
        dev_db_path_old = os.path.join(output_db_dir, f"{db_name}_dev.sqlite")
        if os.path.exists(train_db_path_old):
            os.remove(train_db_path_old)
        if os.path.exists(dev_db_path_old):
            os.remove(dev_db_path_old)
    
    os.makedirs(output_db_dir, exist_ok=True)
    
    # Create paths for train and dev databases
    train_db_path = os.path.join(output_db_dir, f"{db_name}_train.sqlite")
    dev_db_path = os.path.join(output_db_dir, f"{db_name}_dev.sqlite")
    
    print(f"Processing {db_name}...")
    
    # Get all tables
    tables = get_table_names(input_db_path)
    print(f"  Found {len(tables)} tables")
    
    # Create new databases
    train_conn = sqlite3.connect(train_db_path)
    dev_conn = sqlite3.connect(dev_db_path)
    train_cursor = train_conn.cursor()
    dev_cursor = dev_conn.cursor()
    
    # Process each table
    for table in tables:
        print(f"  Splitting table: {table}")
        
        # Create table schema in both databases
        schema = get_table_schema(input_db_path, table)
        train_cursor.execute(schema)
        dev_cursor.execute(schema)
        
        # Get all rows and shuffle
        rows = get_all_rows(input_db_path, table)
        random.shuffle(rows)
        
        # Split rows
        split_idx = int(len(rows) * train_ratio)
        train_rows = rows[:split_idx]
        dev_rows = rows[split_idx:]
        
        print(f"    Total rows: {len(rows)} | Train: {len(train_rows)} | Dev: {len(dev_rows)}")
        
        # Insert rows into respective databases
        if train_rows:
            placeholders = ','.join(['?'] * len(train_rows[0]))
            train_cursor.executemany(f'INSERT INTO "{table}" VALUES ({placeholders})', train_rows)
        
        if dev_rows:
            placeholders = ','.join(['?'] * len(dev_rows[0]))
            dev_cursor.executemany(f'INSERT INTO "{table}" VALUES ({placeholders})', dev_rows)
    
    # Commit and close
    train_conn.commit()
    dev_conn.commit()
    train_conn.close()
    dev_conn.close()
    
    # Copy database_description folder if it exists
    desc_folder = parent_dir / "database_description"
    if desc_folder.exists():
        import shutil
        output_desc_folder = os.path.join(output_db_dir, "database_description")
        shutil.copytree(desc_folder, output_desc_folder, dirs_exist_ok=True)
        print(f"  Copied database_description folder")
    
    print(f"  Created {train_db_path}")
    print(f"  Created {dev_db_path}\n")


def main():
    parser = argparse.ArgumentParser(description='Split BIRD databases into train/dev sets')
    parser.add_argument('input_db', help='Input database path or directory of databases')
    parser.add_argument('output_dir', help='Output directory for split databases')
    parser.add_argument('--train-ratio', type=float, default=0.8, help='Training data ratio (default: 0.8)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed (default: 42)')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite existing output databases')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Process single database or directory
    if os.path.isfile(args.input_db):
        split_database(args.input_db, args.output_dir, args.train_ratio, args.seed, args.overwrite)
    elif os.path.isdir(args.input_db):
        # Process all .sqlite files in directory
        db_files = list(Path(args.input_db).glob('*.sqlite'))
        print(f"Found {len(db_files)} databases to process\n")
        
        for db_file in db_files:
            split_database(str(db_file), args.output_dir, args.train_ratio, args.seed, args.overwrite)
    else:
        print(f"Error: {args.input_db} is not a valid file or directory")
        return 1
    return 0


if __name__ == '__main__':
    exit(main())
"""
cd constraint_extraction
python split_db.py \
  BIRD_dev/california_schools/california_schools.sqlite \
  BIRD_dev_split \
  --train-ratio 0.8 \
  --overwrite 
  """
