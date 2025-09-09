import argparse
import csv
import os
from execute_sql import execute_counterexample_

DONT_CARE = "dontcare"
CORRECT = "correct"
INCORRECT = "incorrect"
UNKNOWN = "unknown"
ERROR = "error"
TIMEOUT = "timeout"

K = 5  # Maximum bound size to consider

def execute_counterexample(counterexample_path, prediction_path):
    if not os.path.exists(counterexample_path):
        return None
    return execute_counterexample_(counterexample_path, "./column_name_mapping.json", "../BIRD_schemas/dev.json", prediction_path)

def get_bounds_info(question_id, folder, prediction_path, results_rows):
    bounds = []
    for b in range(K):
        row = results_rows[int(question_id) * K + b]
        assert(int(row["question_id"]) == int(question_id))
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
            "original_result": row["equivalent"],
            "time_cost": float(row["time_cost"]) if not is_error else 0,
            "counterexample_path": counterexample_path,
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
    ap.add_argument("--question-id", default=None, type=int, help="If set, only process this question ID.")

    
    args = ap.parse_args()
    folder = args.input
    input_csv = args.ex_input
    output_csv = args.output

    with open(os.path.join(folder, "results.csv")) as results_file:
        results_rows = list(csv.DictReader(results_file))

    with open(input_csv, newline='') as infile, open(output_csv, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = ["question_id", "res", "verieql_res_orig", "verieql_res", "bound_size", "counterexample_path", "runtime", "output1", "output2", "generated_sql", "gold_sql"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            question_id = row["question_id"]
            if args.question_id is not None and int(question_id) != args.question_id:
                continue
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
                print(f"Processing question_id {question_id} for {folder}")
                bounds = get_bounds_info(question_id, folder, args.prediction, results_rows)
                deemed_incorrect = any(b["original_result"] in [False, "False"] for b in bounds)
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
                    "verieql_res_orig": INCORRECT if deemed_incorrect else CORRECT,
                    "verieql_res": verieql_res,
                    "bound_size": bound_size,
                    "counterexample_path": os.path.join(folder, f"counterexample_{question_id}_bound{bound_size}.txt"),
                    "runtime": runtime,
                    "output1": output1,
                    "output2": output2,
                    "generated_sql": bounds[0]["generated_sql"],
                    "gold_sql": bounds[0]["gold_sql"],
                })

if __name__ == "__main__":
    main()