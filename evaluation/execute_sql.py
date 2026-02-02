import sqlite3
import json
import re
import os

DONT_CARE = "dontcare"
CORRECT = "correct"
INCORRECT = "incorrect"
UNKNOWN = "unknown"
ERROR = "error"
TIMEOUT = "timeout"


# --- Provided functions ---
def calculate_ex(predicted_res, ground_truth_res):
    if set(predicted_res) != set(ground_truth_res):
        if set(predicted_res) == set() and set(ground_truth_res) == {(None,)}:
            return None
        elif set(ground_truth_res) == set() and set(predicted_res) == {(None,)}:
            return None
        else:
            return INCORRECT

def connect_db(db_path):
    conn = sqlite3.connect(db_path)
    return conn

def execute_sql(predicted_sql, ground_truth, db_path, calculate_func):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute(predicted_sql)
    predicted_res = cursor.fetchall()
    cursor.execute(ground_truth)
    ground_truth_res = cursor.fetchall()
    conn.close()
    res = calculate_func(predicted_res, ground_truth_res)
    return res, predicted_res, ground_truth_res

def execute_model(predicted_sql, ground_truth, db_place, idx):
    try:
        res, predicted_res, ground_truth_res = execute_sql(
            predicted_sql, ground_truth, db_place, calculate_ex
        )
    except Exception as e:
        print("Error executing SQL:", e)
        res = -1
        predicted_res = None
        ground_truth_res = None
    if res == INCORRECT:
        result = predicted_res, ground_truth_res
    else:
        result = None
    return result

# --- Main script ---
def execute_counterexample_(counterexample_path, column_name_mapping_path, dev_json_path, alpha_sql_json_path):
    # Load files
    with open(counterexample_path, "r") as f:
        counterexample = f.read()
    with open(column_name_mapping_path, "r") as f:
        col_map = json.load(f)
    with open(dev_json_path, "r") as f:
        dev_json = json.load(f)
    with open(alpha_sql_json_path, "r") as f:
        alpha_sql_json = json.load(f)

    # Extract question_id from filename
    basename = os.path.basename(counterexample_path)
    match = re.match(r"counterexample_(\d+)_bound\d+", basename)
    if not match:
        raise ValueError("Filename does not match expected pattern.")
    question_id = int(match.group(1))

    db_id = dev_json[question_id]["db_id"]

    database = open(counterexample_path, 'r').readlines()[1:]
    # find the line that starts with "--"
    separator_index = next(i for i, line in enumerate(database) if line.startswith("--"))
    db_def = database[:separator_index]

    mapping = col_map["clean_to_orig"][db_id]

    new_db_def = []
    in_table_def = False
    for line in db_def:
        if line.startswith("CREATE TABLE"):
            in_table_def = True
            if "ORDER" in line:
                line = line.replace("ORDER", "`ORDER`")
            new_db_def.append(line)
        elif in_table_def:
            if line.startswith(");"):
                in_table_def = False
                new_db_def.append(line)
            else:
                parts = line.split()
                assert(len(parts) == 2)
                col_name = parts[0]
                new_column_name = mapping[col_name]
                new_db_def.append(f"\"{new_column_name.upper()}\" {parts[1]}")
        else:
            if "ORDER" in line:
                line = line.replace("ORDER", "`ORDER`")
            if "JOURNEY INTO NYX HERO'S PATH" in line:
                line = line.replace("JOURNEY INTO NYX HERO'S PATH", "JOURNEY INTO NYX HERO''S PATH")
            if "ANCESTOR'S CHOSEN" in line:
                line = line.replace("ANCESTOR'S CHOSEN", "ANCESTOR''S CHOSEN")
            if "Woman's" in line:
                line = line.replace("Woman's", "Woman''s")
            if "Women's" in line:
                line = line.replace("Women's", "Women''s")
            if "': " in line and "{'" in line:
                line = re.sub(r"'([^']+)':", r"''\1'':", line)
            if "WOMAN'S" in line:
                line = line.replace("WOMAN'S", "WOMAN''S")
            if "WOMEN'S" in line:
                line = line.replace("WOMEN'S", "WOMEN''S")
            new_db_def.append(line)
    db_def = "\n".join(new_db_def)
    # Dump to sqlite database

    db_path = "temp.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for stmt in db_def.split(";"):
        stmt = stmt.strip()
        if stmt:
            try:
                #print(question_id, stmt)
                cursor.execute(stmt)
            except sqlite3.OperationalError as e:
                print(f"=== SQL ERROR for question {question_id} ===")
                print(f"Error: {e}")
                print(f"Statement: {stmt}")
                print("=" * 50)
                raise
    conn.commit()
    conn.close()

    # Get sql1 and sql2
    sql1 = alpha_sql_json[str(question_id)]
    sql2 = dev_json[question_id]["SQL"]

    if "\t----- bird" in sql1:
        #print("found bird in sql1")
        sql1 = sql1.split("\t----- bird")[0]

    # Execute both queries
    return execute_model(sql1.upper(), sql2.upper(), db_path, question_id)

