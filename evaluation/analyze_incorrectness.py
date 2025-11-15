#!/usr/bin/env python3
"""
Script to analyze incorrectness across CSV files and generate a histogram.

Incorrectness is defined as either:
1. res is 'incorrect' 
2. verieql_res is 'incorrect' (if the column exists and is not empty)

The script creates a dictionary mapping question_id to the count of incorrectness
across all CSV files, then generates a histogram.
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt
import os
from collections import defaultdict
import glob
import numpy as np

def analyze_incorrectness(incorrects, csv_folder_path, ex):
    """
    Analyze incorrectness across all CSV files in the given folder.
    
    Args:
        csv_folder_path (str): Path to folder containing CSV files
        
    Returns:
        dict: Dictionary mapping question_id to incorrectness count
    """

    # Dictionary to store incorrectness count for each question_id
    incorrectness_count = defaultdict(int)

    # Find all CSV files in the folder
    csv_files = glob.glob(os.path.join(csv_folder_path, "*.csv"))

    print(f"Found {len(csv_files)} CSV files to analyze:")
    for csv_file in csv_files:
        print(f"  - {os.path.basename(csv_file)}")

    # Process each CSV file
    for csv_file in csv_files:
        print(f"\nProcessing: {os.path.basename(csv_file)}")

        try:
            # Read CSV file
            df = pd.read_csv(csv_file)

            # Check if required columns exist
            if 'question_id' not in df.columns or 'res' not in df.columns:
                print(f"  Warning: Missing required columns in {csv_file}")
                continue

            # Process each row
            for _, row in df.iterrows():
                question_id = row['question_id']
                if int(question_id) not in incorrects:
                    continue
                #if question_id not in incorrectness_count:
                #    incorrectness_count[question_id] = 0
                is_incorrect = False

                if ex:
                    # Check if res is incorrect
                    if row['res'] == "incorrect":
                        is_incorrect = True

                if 'verieql_res' in df.columns:
                    if row['verieql_res'] == 'incorrect':
                        is_incorrect = True

                # Increment count if incorrect
                if is_incorrect:
                    incorrectness_count[question_id] += 1

            print(f"  Processed {len(df)} rows")

        except Exception as e:
            print(f"  Error processing {csv_file}: {e}")

    return dict(incorrectness_count)

import matplotlib.pyplot as plt
import numpy as np

def create_histogram(incorrectness_data, output_path=None):
    """
    Create and display bar plot of incorrectness counts.
    
    Args:
        incorrectness_data (dict): Dictionary mapping question_id to incorrectness count
        output_path (str, optional): Path to save the bar plot image
    """

    counts = list(incorrectness_data.values())
    if counts:
        # Count how many questions fall into each incorrectness value
        values, frequencies = np.unique(counts, return_counts=True)

        # Make the plot taller and wider
        plt.figure(figsize=(8, 5))  # Increased height from 8 to 14

        # Make bars thinner by setting width
        bar_width = 0.6  # Default is 0.8, so 0.4 is thinner
        bars = plt.bar(values, frequencies, width=bar_width, alpha=0.7, edgecolor='black')

        # Even larger fonts for labels
        plt.xlabel('# Text-to-SQL methods', fontsize=32)
        plt.ylabel('# questions', fontsize=32)

        #plt.yscale('log')  # Use log scale for y-axis
        # Set the y-axis range to be larger (e.g., from 0.8 to 10x the max frequency)
        min_y = 0.8
        max_y = max(frequencies) * 1.15 if len(frequencies) > 0 else 10
        plt.ylim(min_y, max_y)
        plt.grid(True, axis="y", alpha=0.3, which='both')
        plt.xticks(values, fontsize=26)   # One tick per integer
        # Set y-ticks every 50 (e.g., 50, 100, 150, ...) but do not include 0
        if max_y >= 50:
            yticks = np.arange(50, max_y + 1, 50)
            plt.yticks(yticks, fontsize=26)
        else:
            plt.yticks(fontsize=26)

        # Add value labels above each bar (show only if freq > 0)
        for bar, freq in zip(bars, frequencies):
            height = bar.get_height()
            if freq > 0:
                plt.text(bar.get_x() + bar.get_width()/2, height,
                         f"{int(freq)}", ha='center', va='bottom', fontsize=24)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"Bar plot saved to: {output_path}")

        plt.show()
    else:
        print("No incorrectness data to plot.")

    return counts
    

def print_summary_statistics(incorrectness_data):
    """
    Print summary statistics about the incorrectness data.
    
    Args:
        incorrectness_data (dict): Dictionary mapping question_id to incorrectness count
    """
    
    counts = list(incorrectness_data.values())
    
    print("\n" + "="*50)
    print("SUMMARY STATISTICS")
    print("="*50)
    print(f"Total number of questions: {len(incorrectness_data)}")
    print(f"Total incorrectness instances: {sum(counts)}")
    print(f"Questions with no incorrectness: {sum(1 for c in counts if c == 0)}")
    print(f"Questions with at least one incorrectness: {sum(1 for c in counts if c > 0)}")
    
    if counts:
        print(f"Maximum incorrectness for a single question: {max(counts)}")
        print(f"Average incorrectness per question: {sum(counts) / len(counts):.2f}")
        
        # Distribution by incorrectness count
        from collections import Counter
        count_distribution = Counter(counts)
        print(f"\nDistribution of incorrectness counts:")
        sum_ = 0
        for incorrectness_count in sorted(count_distribution.keys()):
            num_questions = count_distribution[incorrectness_count]
            sum_ += num_questions
            print(f"  {incorrectness_count} incorrectness: {num_questions} questions")
        print(f"  Total questions counted: {sum_}")

def main():
    # Set the folder path
    csv_folder_path = sys.argv[1]
    if len(sys.argv) != 5:
        incorrects = set([i for i in range(1, 1533)])  # Default to question IDs 1 to 100
    else:
        target_path = sys.argv[4]
        
        print("Starting analysis of CSV files...")

        df = pd.read_csv(target_path)

        # Process each row
        incorrects = set()
        for _, row in df.iterrows():
            question_id = row['question_id']
            if row['res'] == "incorrect":
                incorrects.add(int(question_id))

    # Analyze incorrectness
    incorrectness_data = analyze_incorrectness(incorrects, csv_folder_path, len(sys.argv) == 5)
    
    # Print summary statistics
    print_summary_statistics(incorrectness_data)
    
    # Create histogram
    output_path = sys.argv[2]
    create_histogram(incorrectness_data, output_path)
    
    # Optionally save the data to a file
    import json
    data_output_path = sys.argv[3]
    with open(data_output_path, 'w') as f:
        json.dump(incorrectness_data, f, indent=2)
    print(f"Incorrectness data saved to: {data_output_path}")

if __name__ == "__main__":
    main()
