import argparse
import csv
import json
import os
from  execute_sql import execute_counterexample_


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

def count_correct_and_not_incorrect(rows, orig):
    if orig:
        filtered = [row for row in rows if row["res"] == "correct" and row["verieql_res_orig"] != "incorrect"]
    else:
        filtered = [row for row in rows if row["res"] == "correct" and row["verieql_res"] != "incorrect"]
    return len(filtered), len(rows), len(filtered) / len(rows) if rows else 0


# --- Provided functions ---
def calculate_ex(predicted_res, ground_truth_res):
    if set(predicted_res) != set(ground_truth_res):
        return INCORRECT

def main():

    ap = argparse.ArgumentParser(
        description="Verify VeriEQL counterexamples from a CSV column containing the full block."
    )
    ap.add_argument("csv_path", help="Path to the prediction.")
    ap.add_argument("--prediction", default=None)
    ap.add_argument("--orig", action="store_true")

    args = ap.parse_args()

    if not os.path.exists(args.csv_path):
        print(f"File {args.csv_path} does not exist.")
        return

    with open(args.csv_path, newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # 1. Occurrence and frequency of res == "correct"
    correct_count, total_count, correct_freq = count_correct_rows(rows)
    print(f'EX": {correct_count}/{total_count} ({correct_freq:.2%})')

    # 2. If verieql_res column exists, occurrence and frequency of res == "correct" and verieql_res != "incorrect"
    if "verieql_res" in reader.fieldnames:
        if args.orig:
            filtered_count_orig, _, filtered_freq = count_correct_and_not_incorrect(rows, True)
        filtered_count, _, filtered_freq = count_correct_and_not_incorrect(rows, False)
        print(f'EX + VeriEQL + Validation": {filtered_count}/{total_count} ({filtered_freq:.2%})')
        print(f"Verification success rate: {(filtered_count_orig / filtered_count):.2%}")

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
