import csv
import sys
import numpy as np

file_path = sys.argv[1]

time = []
with open(file_path, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if row.get('verieql_res', '').strip().lower() == 'incorrect':
            try:
                runtime = float(row.get('runtime', 0))
                time.append(runtime)
            except ValueError:
                continue

print(f"Average runtime for incorrect: {np.mean(time) if time else 'N/A'}")
print(f"Median runtime for incorrect: {np.median(time) if time else 'N/A'}")