import argparse
import csv
import json
import os
import re
import sqlite3


DONT_CARE = "dontcare"
CORRECT = "correct"
INCORRECT = "incorrect"
UNKNOWN = "unknown"
ERROR = "error"
TIMEOUT = "timeout"

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def count_correct_rows(rows):
    correct_rows = [row for row in rows if row.get("res") == "correct"]
    return len(correct_rows), len(rows), len(correct_rows) / len(rows) if rows else 0

def count_correct_and_not_incorrect(rows):
    filtered = [row for row in rows if row["res"] == "correct" and row["verieql_res"] != "incorrect"]
    return len(filtered), len(rows), len(filtered) / len(rows) if rows else 0


# --- Provided functions ---
def calculate_ex(predicted_res, ground_truth_res):
    if set(predicted_res) != set(ground_truth_res):
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
                new_db_def.append(f"\"{mapping[col_name]}\" {parts[1]}")
        else:
            if "ORDER" in line:
                line = line.replace("ORDER", "`ORDER`")
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
            cursor.execute(stmt)
    conn.commit()
    conn.close()

    # Get sql1 and sql2
    sql1 = alpha_sql_json[str(question_id)]
    sql2 = dev_json[question_id]["SQL"]

    # Execute both queries
    return execute_model(sql1, sql2, db_path, question_id)

def main():

    ap = argparse.ArgumentParser(
        description="Verify VeriEQL counterexamples from a CSV column containing the full block."
    )
    ap.add_argument("csv_path", help="Path to the prediction.")
    ap.add_argument("--prediction", default=None)

    args = ap.parse_args()

    with open(args.csv_path, newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # 1. Occurrence and frequency of res == "correct"
    correct_count, total_count, correct_freq = count_correct_rows(rows)
    print(f'EX": {correct_count}/{total_count} ({correct_freq:.2%})')

    # 2. If verieql_res column exists, occurrence and frequency of res == "correct" and verieql_res != "incorrect"
    if "verieql_res" in reader.fieldnames:
        filtered_count, _, filtered_freq = count_correct_and_not_incorrect(rows)
        print(f'EX + VeriEQL + Validation": {filtered_count}/{total_count} ({filtered_freq:.2%})')

    # 3. If prediction file is provided, execute counterexample DBs and confirm result is not None
    if args.prediction is not None:
        print(f"Re-validating the counter-examples for {args.prediction}")
        validated = 0
        for row in rows:
            if row["verieql_res"] == "incorrect":
                ce_path = row.get("counterexample_path")
                output1, output2 = execute_counterexample_(ce_path, "./column_name_mapping.json", "../BIRD_schemas/dev.json", args.prediction)
                if output1 != output2:
                    validated += 1
                else:
                    print("Failed to validate counter-example for question_id:", row["question_id"])
                    assert(False)
        print(f"Validated {validated} VeriEQL counter-examples")

if __name__ == "__main__":
    main()