import argparse
import csv
import os
import json
import re
import sqlite3

DONT_CARE = "dontcare"
CORRECT = "correct"
INCORRECT = "incorrect"
UNKNOWN = "unknown"
ERROR = "error"
TIMEOUT = "timeout"


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


def execute_counterexample(counterexample_path, prediction_path):
    if not os.path.exists(counterexample_path):
        return None
    return execute_counterexample_(counterexample_path, "./column_name_mapping.json", "../BIRD_schemas/dev.json", prediction_path)

def get_bounds_info(question_id, folder, prediction_path):
    reader = csv.DictReader(open(os.path.join(folder, "results.csv")))
    bounds = []
    for row in reader:
        if row["question_id"] != question_id:
            continue
        else:
            is_error = row["equivalent"] == "ERROR"
            is_correct = row["equivalent"] in ["True", True]
            is_incorrect = row["equivalent"] in ["False", False]
            is_timeout = row["equivalent"] == "Unknown"
            bound_size = int(row["bound_size"])
            counterexample_path = os.path.join(folder, f"counterexample_{question_id}_bound{bound_size}.txt")
            results = execute_counterexample(counterexample_path, prediction_path)
            if results is None:
                is_incorrect = False
            else:
                output1, output2 = results

            if is_error:
                result = ERROR
            elif is_correct:
                result = CORRECT
            elif is_incorrect:
                result = INCORRECT
            elif is_timeout:
                result = TIMEOUT
            else:
                result = UNKNOWN
            bounds.append({
                "bound_size": bound_size, 
                "result": result,
                "time_cost": float(row["time_cost"]) if not is_error else 0,
                "output1": output1 if results else "",
                "output2": output2 if results else "",
                "generated_sql": row["generated_sql"],
                "gold_sql": row["gold_sql"],
            })
    return bounds

def compute_verieql_res(bounds):
    equivalents = [b["result"] for b in bounds]
    if any(eq == ERROR for eq in equivalents):
        return ERROR
    if any(eq == INCORRECT for eq in equivalents):
        return INCORRECT
    return UNKNOWN

def compute_runtime(bounds, verieql_res, bound_size):
    if verieql_res in [ERROR, UNKNOWN]:
        return 0
    else:
        assert(verieql_res == INCORRECT)
        return sum(b["time_cost"] for b in bounds if 1 <= b["bound_size"] <= bound_size)

def main():
    ap = argparse.ArgumentParser(
        description="Verify VeriEQL counterexamples from a CSV column containing the full block."
    )
    ap.add_argument("input", help="Path to directory of VeriEQL results.")
    ap.add_argument("prediction", help="Path to the prediction.")
    ap.add_argument("ex_input", help="Path to CSV with EX results.")
    ap.add_argument("output", help="Output CSV path.")
    
    args = ap.parse_args()
    folder = args.input
    input_csv = args.ex_input
    output_csv = args.output

    with open(input_csv, newline='') as infile, open(output_csv, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = ["question_id", "res", "verieql_res", "bound_size", "runtime", "output1", "output2", "generated_sql", "gold_sql"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            question_id = row["question_id"]
            res = row["res"]
            if res == "incorrect":
                writer.writerow({
                    "question_id": question_id,
                    "res": res,
                    "verieql_res": DONT_CARE,
                    "bound_size": -1,
                    "runtime": 0
                })
            else:
                assert(res == "correct")
                bounds = get_bounds_info(question_id, folder, args.prediction)
                valid_bounds = [b for b in bounds if b["result"] == INCORRECT]
                bound_size = min([b["bound_size"] for b in valid_bounds], default=-1)
                output1, output2 = "", ""
                for b in valid_bounds:
                    if b["bound_size"] == bound_size:
                        output1, output2 = b["output1"], b["output2"]
                        break
                verieql_res = compute_verieql_res(bounds)
                runtime = compute_runtime(bounds, verieql_res, bound_size)
                writer.writerow({
                    "question_id": question_id,
                    "res": res,
                    "verieql_res": verieql_res,
                    "bound_size": bound_size,
                    "runtime": runtime,
                    "output1": output1,
                    "output2": output2,
                    "generated_sql": bounds[0]["generated_sql"],
                    "gold_sql": bounds[0]["gold_sql"],
                })

if __name__ == "__main__":
    main()