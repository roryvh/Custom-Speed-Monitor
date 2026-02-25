import matplotlib.pyplot as plt
import numpy as np
import csv
from glob import glob
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def read_csv(file_path):
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        # Skip the header
        next(reader)

        data = [row for row in reader]
    
    data = np.array(data).astype(np.float32)
    
    return data

if __name__ == "__main__":
    # Read all CSV files in the current directory
    csv_files = sorted(glob(os.path.join(SCRIPT_DIR, "data", "*.csv")))
    print(f"Found {len(csv_files)} CSV files.")
    print(f"CSV files: {csv_files}")

    os.makedirs(os.path.join(SCRIPT_DIR, "plots"), exist_ok=True)
    
    for csv_file in csv_files:
        data = read_csv(csv_file)
        # print(data)
        print(f"Data from {csv_file} is of shape: {data.shape}")
        
        # Plot the velocity data, plotting a different line for each column
        plt.figure(figsize=(10, 6))
        for i in range(data.shape[1]):
            plt.plot(data[:, i], label=f"Column {i+1}")
        plt.title(f"Velocity vs Time for {os.path.basename(csv_file)}")
        plt.xlabel('Iteration')
        plt.ylabel('Velocity (m/s)')

        # Setup y min to be +- 5 m/s around the min and max of the data
        y_padding = 1
        y_min = np.min(data, axis=None)
        y_max = np.max(data, axis=None)
        plt.ylim(y_min - y_padding, y_max + y_padding)

        plt.grid()
        plt.xticks(range(0, data.shape[0] + 1, 1))
        plt.legend()
        plt.savefig(os.path.join(SCRIPT_DIR, "plots", os.path.basename(csv_file).replace('.csv', '.png')))
        plt.close()
        print(f"Plot saved for {csv_file}")

         # --- Box plot ---
        plt.figure(figsize=(10, 6))
        plt.boxplot(
            [data[:, i] for i in range(data.shape[1])],
            labels=[f"v{i+1}" for i in range(data.shape[1])]
        )
        plt.title(f"Box Plot for {os.path.basename(csv_file)}")
        plt.xlabel('Beam Break Interval')
        plt.ylabel('Velocity (m/s)')
        plt.grid(axis='y')
        plt.savefig(os.path.join(SCRIPT_DIR, "plots", os.path.basename(csv_file).replace('.csv', '_boxplot.png')))
        plt.close()
        print(f"Box plot saved for {csv_file}")
    
