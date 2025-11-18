import argparse
import csv
import os

ERROR = "error"
OK = "ok"

K = 5

def get_bounds_info(question_id, folder, results_rows):
    bounds = []
    for b in range(K):
        row = results_rows[int(question_id) * K + b]

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

    with open(os.path.join(folder, "results.csv")) as results_file:
        results_rows = list(csv.DictReader(results_file))

    num_relevant = 0
    num_supported = 0
    output_rows = []
    with open(input_csv, newline='') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            question_id = row["question_id"]
            res = row["res"]
            if res == "incorrect":
                continue
            else:
                assert(res == "correct")
                bounds = get_bounds_info(question_id, folder, results_rows)
                has_error = any(b["result"] == ERROR for b in bounds)
                error_msg = ""
                if has_error:
                    # Find the first error message from the corresponding rows
                    for b in range(K):
                        row_idx = int(question_id) * K + b
                        if results_rows[row_idx]["equivalent"] == "ERROR":
                            error_msg = results_rows[row_idx].get("error", "")
                            break
                supported = not has_error
                output_rows.append({
                    "question_id": question_id,
                    "supported": str(supported),
                    "error": error_msg
                })
                if supported:
                    num_supported += 1
                num_relevant += 1

    print(f"Coverage: {num_supported}/{num_relevant} ({num_supported/num_relevant:.2%})")

    # Write output CSV
    output_csv_path = os.path.join(folder, "coverage_supported.csv")
    with open(output_csv_path, "w", newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=["question_id", "supported", "error"])
        writer.writeheader()
        for row in output_rows:
            writer.writerow(row)


if __name__ == "__main__":
    main()