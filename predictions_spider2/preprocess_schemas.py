# -*- coding:utf-8 -*-

import json
import os
from constants import PROJ_PATH
import glob
import csv
import re


def get_sqlite_dbs(file):
    ID2DBS = {}
    with open(file, 'r') as reader:
        for line in map(json.loads, reader):
            ID2DBS[line["instance_id"]] = line["db"].replace('-', '_')
    return ID2DBS


def get_gold_queries(SQLite_ids):
    ID2GOLD_QUERY = {}
    for id in SQLite_ids.keys():
        file = os.path.join(PROJ_PATH, f"benchmarks/Spider2/spider2-lite/evaluation_suite/gold/sql/{id}.sql")
        if not os.path.exists(file):
            continue
        with open(file, 'r') as reader:
            gold_query = reader.read().strip()
        ID2GOLD_QUERY[id] = gold_query
    return ID2GOLD_QUERY


SQLITE_INDEX_FILE = os.path.join(PROJ_PATH, "benchmarks/spider2_lite/cleaned_predictions_omni/spider2-lite.jsonl")
ID2DBS = get_sqlite_dbs(SQLITE_INDEX_FILE)
ID2GOLD_QUERY = get_gold_queries(ID2DBS)


def polish_gold_query(query):
    return query.replace("'number of product being viewed'", 'number_of_product_being_viewed') \
        .replace("'number added to the cart'", 'number_added_to_the_cart') \
        .replace("'without being purchased in cart'", 'without_being_purchased_in_cart') \
        .replace("'count of actual purchases'", 'count_of_actual_purchases')


GOLD_QUERIES = {}
for i, id in enumerate(ID2DBS.keys()):
    if id in ID2GOLD_QUERY:
        query = ID2GOLD_QUERY[id]
        lines = []
        for line in map(str.strip, query.split('\n')):
            comment_idx = line.find("--")
            if comment_idx != -1:
                line = line[:comment_idx]
            lines.append(line)
        lines = [line for line in lines if len(line) > 0]
        query = ' '.join(lines)
        query = polish_gold_query(query)
    else:
        query = None
    GOLD_QUERIES[i] = query

GOLD_QUERIES_FILE = "/home/yang/Dropbox/codes/VeriEQL/predictions_spider2/gold_queries.json"
# with open(GOLD_QUERIES_FILE, 'w') as writer:
#     json.dump(GOLD_QUERIES, writer)

INDEX_TO_DATABASE_FILE = os.path.join(PROJ_PATH, "Spider2_schemas/index_to_database.json")
# IDX2DB = {}
# for id, db in enumerate(ID2DBS.values()):
#     IDX2DB[id] = db
with open(INDEX_TO_DATABASE_FILE, 'r') as reader:
    IDX2DB = json.load(reader)

TABLE_TO_COLUMNS_FILE = "/home/yang/Dropbox/codes/VeriEQL/Spider2_schemas/table_to_columns.json"


def refine_type(type):
    type = str.upper(type)
    if type in {"NUMBER", "NUMERIC", "INTEGER", "BINARY", "", "BIGINT", "SMALLINT", "NUM"} \
            or any(type.startswith(t) for t in ["INT", "NUMERIC"]):
        return "INTEGER"
    elif type in {"REAL"} or any(type.startswith(t) for t in ["DECIMAL", "FLOAT"]):
        return "REAL"
    elif type in {"STRING", "TEXT", "POINT", "JSONB", "BLOB", "BLOB SUB_TYPE TEXT"} or \
            any(type.startswith(t) for t in ["VARCHAR", "CHAR", "NVARCHAR"]):
        return "VARCHAR"
    elif type in {"DATE", "TIME", "TIMESTAMP", "TIMESTAMP_NTZ", "TIMESTAMP_LTZ", "DATETIME", "TIMESTAMP WITH TIME ZONE"}:
        return "DATE"
    elif type in {"BOOLEAN"}:
        return "BOOLEAN"
    else:
        raise NotImplementedError(f"Unknown type: {type}")


TABLE_DIR = os.path.join(PROJ_PATH, "benchmarks/Spider2/spider2-lite/resource/databases/sqlite")
TABLE2COLS = {}
DATE_PATTERNS = ["\d{4}-\d{1,2}-\d{1,2}", "\d{1,2}/\d{1,2}/\d{1,2}"]
for table in os.listdir(TABLE_DIR):
    # if table in {'imdb_movies'}:  # this table is never used
    #     continue
    schema = {}
    table_ddl_file = os.path.join(TABLE_DIR, table, "DDL.csv")
    with open(table_ddl_file, 'r') as reader:
        csv_reader = csv.reader(reader)
        next(csv_reader)
        for (t_name, t_schema) in csv_reader:
            is_date_type = {}
            with open(os.path.join(TABLE_DIR, table, f"{t_name}.json"), "r") as f:
                example = json.load(f)
                if len(example["sample_rows"]) > 0:
                    keys = list(example["sample_rows"][0].keys())
                    num_example = len(example["sample_rows"])
                    for key in keys:
                        if any(any(re.match(pattern, example["sample_rows"][i][key]) for pattern in DATE_PATTERNS) \
                               for i in range(num_example) if isinstance(example["sample_rows"][i][key], str)):
                            is_date_type[str.upper(key)] = True
                        else:
                            is_date_type[str.upper(key)] = False

            t_name, t_schema = str.upper(t_name), str.upper(t_schema)
            schema[t_name] = {}
            for line in t_schema.split('\n')[1:-1]:
                line = line.strip().strip(',').strip()
                if ' ' in line:
                    if table in {'imdb_movies'}:
                        attr, type = line.rsplit(' ', 1)
                    else:
                        attr, type = line.split(' ', 1)
                else:
                    attr, type = line, "INTEGER"
                if is_date_type.get(attr, False):
                    schema[t_name][attr] = "DATE"
                else:
                    schema[t_name][attr] = refine_type(type)
    TABLE2COLS[str.upper(table)] = schema

with open(TABLE_TO_COLUMNS_FILE, 'w') as write:
    json.dump(TABLE2COLS, write)

SCHEMAS = {}
for id, db in IDX2DB.items():
    db = str.upper(db)
    assert db in TABLE2COLS, db
    schema = TABLE2COLS[db]
    SCHEMAS[id] = schema

INDEX_TO_SCHEMAS_FILE = "/home/yang/Dropbox/codes/VeriEQL/Spider2_schemas/index_to_schemas.json"
with open(INDEX_TO_SCHEMAS_FILE, 'w') as writer:
    json.dump(SCHEMAS, writer)
