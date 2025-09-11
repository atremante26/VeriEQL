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

def analyze_incorrectness(csv_folder_path):
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
                #if question_id not in incorrectness_count:
                #    incorrectness_count[question_id] = 0
                is_incorrect = False
                
                # Check if res is incorrect
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

        plt.figure(figsize=(12, 8))
        bars = plt.bar(values, frequencies, alpha=0.7, edgecolor='black')

        # Larger fonts for labels
        plt.xlabel('# predictions deemed correct by EX and incorrect by SpotIt', fontsize=20)
        plt.ylabel('# questions', fontsize=20)

        plt.grid(True, axis="y", alpha=0.3)
        plt.xticks(values, fontsize=20)   # One tick per integer
        plt.yticks(fontsize=20)

        # Add value labels above each bar
        for bar, freq in zip(bars, frequencies):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2, height,
                     f"{int(freq)}", ha='center', va='bottom', fontsize=20)

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
    
    print("Starting analysis of CSV files...")
    
    # Analyze incorrectness
    incorrectness_data = analyze_incorrectness(csv_folder_path)
    
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
