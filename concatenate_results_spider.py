#!/usr/bin/env python3
"""
Script to concatenate results from multiple slurm-* directories.
Iterates through slurm-* directories in numerical order and concatenates out.csv files.
If out.csv is missing, extracts relevant information from output.log and run.out.
"""

import os
import re
import csv
import glob
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple


def extract_slurm_number(dirname: str) -> int:
    """Extract the slurm number from directory name."""
    match = re.search(r'slurm-(\d+)', dirname)
    if match:
        return int(match.group(1))
    return 0


def parse_output_log(log_file: str) -> Optional[Dict]:
    """Parse output.log to extract relevant information."""
    with open(log_file, 'r') as f:
        content = f.read()
        
    # Get the line that contains [runlim] argv[3]:
    argv3_match = re.search(r'^\[runlim\] argv\[2\]:\s*(.+)$', content, re.MULTILINE)
    question_id = int(argv3_match.group(1).strip().split()[-1])

    # Get the line that contains [runlim] argv[5]:
    argv4_match = re.search(r'^\[runlim\] argv\[3\]:\s*(.+)$', content, re.MULTILINE)
    bound_size = int(argv4_match.group(1).strip().split()[-1])


    # Extract time information
    time_match = re.search(r'time:\s+([\d.]+)\s+seconds', content)
    time_cost = float(time_match.group(1)) if time_match else 0.0
        
    return {
        'bound_size': bound_size,
        'question_id': question_id,
        'equivalent': 'Unknown',
        'error': '',
        'time_cost': time_cost,
        'generated_sql': 'N/A',
        'gold_sql': 'N/A'
    }



def process_slurm_directory(slurm_dir: str, output_dir: str) -> List[Dict]:
    """Process a single slurm directory and return list of result rows."""
    results = []
    
    out_csv_file = os.path.join(slurm_dir, 'out.csv')
    output_log_file = os.path.join(slurm_dir, 'output.log')
    
    # If out.csv exists, read it directly
    if os.path.exists(out_csv_file):
        try:
            with open(out_csv_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    results.append(row)
        except Exception as e:
            print(f"Warning: Could not read {out_csv_file}: {e}")    
    
    # If no results from out.csv, try to extract from log files
    if not results:
        print(f"Processing {slurm_dir} from log files...")
        
        log_data = parse_output_log(output_log_file) if os.path.exists(output_log_file) else {}
        
        # Prefer data from run.out if available, otherwise use output.log
        results.append(log_data)
    
    # Check if results["equivalent"] is False
    for result in results:
        if result.get('equivalent') == 'False':
            question_id = result.get('question_id')
            bound = result.get('bound_size')
            # assert that counterexample.txt exists
            counterexample_file = os.path.join(slurm_dir, 'counterexample.txt')
            if os.path.exists(counterexample_file):
                # copy counterexample.txt to output_dir with new name
                new_counterexample_file = os.path.join(output_dir, f'counterexample_{question_id}_bound{bound}.txt')
                with open(counterexample_file, 'r') as src, open(new_counterexample_file, 'w') as dst:
                    dst.write(src.read())
                print(f"Copied counterexample to {new_counterexample_file}")
    return results


def main():
    parser = argparse.ArgumentParser(description='Concatenate results from slurm-* directories')
    parser.add_argument('input_dir', help='Input directory containing slurm-* subdirectories')
    parser.add_argument('output_dir', help='Output CSV file path')
    
    args = parser.parse_args()
    
    input_path = Path(args.input_dir)
    if not input_path.exists():
        print(f"Error: Input directory {input_path} does not exist")
        return 1

    # create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    # Output file is a csv in the output_dir called results.csv
    output_file = os.path.join(output_dir, 'results.csv')
    
    # Find all slurm-* directories
    slurm_dirs = []
    for item in input_path.iterdir():
        if item.is_dir() and item.name.startswith('slurm-'):
            slurm_dirs.append(str(item))
    
    if not slurm_dirs:
        print(f"Error: No slurm-* directories found in {input_path}")
        return 1
    
    # Sort directories by slurm number
    slurm_dirs.sort(key=extract_slurm_number)

    all_results = []
    processed_count = 0
    
    for slurm_dir in slurm_dirs:
        print(f"Processing {os.path.basename(slurm_dir)}...")

        results = process_slurm_directory(slurm_dir, output_dir)
        if results:
            all_results.extend(results)
            processed_count += 1
    
    if not all_results:
        print("Error: No results found in any directory")
        return 1
    
    # Write concatenated results
    try:
        with open(output_file, 'w', newline='') as f:
            if all_results:
                fieldnames = all_results[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_results)
        
        print(f"Successfully wrote {len(all_results)} rows to {output_file}")
        print(f"Processed {processed_count} out of {len(slurm_dirs)} directories")
        
    except Exception as e:
        print(f"Error writing output file: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
