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
def execute_counterexample_(counterexample_path):
    # Load files
    with open(counterexample_path, "r") as f:
        counterexample = f.read()

    # Extract question_id from filename
    basename = os.path.basename(counterexample_path)
    match = re.match(r"counterexample_(\d+)_bound\d+", basename)
    if not match:
        raise ValueError("Filename does not match expected pattern.")

    database = open(counterexample_path, 'r').readlines()[1:]
    # find the line that starts with "--"
    separator_index = next(i for i, line in enumerate(database) if line.startswith("--"))
    db_def = database[:separator_index]

    new_db_def = []
    for line in db_def:
        if line.startswith("CREATE TABLE"):
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
            #print(question_id, stmt)
            cursor.execute(stmt)
    conn.commit()
    conn.close()

    # Get sql1 and sql2
    sql1 = None
    sql2 = None
    lookForSQL = False
    for line in database:
        if "----sql1----" in line:
            lookForSQL = True
        if lookForSQL and not line.startswith("--"):
            if sql1 is None:
                sql1 = line
            else:
                sql2 = line
    assert(sql1 is not None and sql2 is not None)
    
    # Execute both queries
    return execute_model(sql1.upper(), sql2.upper(), db_path)

