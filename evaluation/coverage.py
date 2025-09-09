import argparse
import csv
import os

ERROR = "error"
OK = "ok"

def get_bounds_info(question_id, folder):
    reader = csv.DictReader(open(os.path.join(folder, "results.csv")))
    bounds = []
    for row in reader:
        if row["question_id"] != question_id:
            continue
        else:
            is_error = row["equivalent"] == "ERROR"

            if is_error:
                result = ERROR
            else:
                result = OK
            bounds.append({
                "result": result,
            })
    return bounds

def main():
    ap = argparse.ArgumentParser(
        description="Verify VeriEQL counterexamples from a CSV column containing the full block."
    )
    ap.add_argument("input", help="Path to directory of VeriEQL results.")
    ap.add_argument("ex_input", help="Path to CSV with EX results.")

    args = ap.parse_args()
    folder = args.input
    input_csv = args.ex_input

    if not os.path.exists(folder):
        print(f"Folder {folder} does not exist.")
        return

    num_relevant = 0
    num_supported = 0
    with open(input_csv, newline='') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            question_id = row["question_id"]
            res = row["res"]
            if res == "incorrect":
                continue
            else:
                assert(res == "correct")
                bounds = get_bounds_info(question_id, folder)
                has_error = any(b["result"] == ERROR for b in bounds)
                if not has_error:
                    num_supported += 1
                else:
                    print(f"Question {question_id} has errors in bounds.")
                num_relevant += 1

    print(f"Coverage: {num_supported}/{num_relevant} ({num_supported/num_relevant:.2%})")


if __name__ == "__main__":
    main()