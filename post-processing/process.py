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
    
    # Define a consistent color map for all plots
    # We need to know the number of intervals from the first file to set the color map size
    if csv_files:
        num_intervals = read_csv(csv_files[0]).shape[1]
        colors = plt.cm.get_cmap('tab10', num_intervals)
    else:
        num_intervals = 0
        colors = None

    for csv_file in csv_files:
        data = read_csv(csv_file)
        # print(data)
        print(f"Data from {csv_file} is of shape: {data.shape}")
        
        # Plot the velocity data, plotting a different line for each column
        plt.figure(figsize=(10, 6))
        for i in range(data.shape[1]):
            plt.plot(data[:, i], label=f"Column {i+1}", color=colors(i))
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
        box = plt.boxplot(
            [data[:, i] for i in range(data.shape[1])],
            labels=[f"v{i+1}" for i in range(data.shape[1])],
            patch_artist=True  # Enable filling boxes with color
        )
        
        # Set colors for each box
        for patch, i in zip(box['boxes'], range(num_intervals)):
            patch.set_facecolor(colors(i))

        plt.title(f"Box Plot for {os.path.basename(csv_file)}")
        plt.xlabel('Beam Break Interval')
        plt.ylabel('Velocity (m/s)')
        plt.grid(axis='y')
        plt.savefig(os.path.join(SCRIPT_DIR, "plots", os.path.basename(csv_file).replace('.csv', '_boxplot.png')))
        plt.close()
        print(f"Box plot saved for {csv_file}")

    # --- Aggregate Scatter Plot ---
    # This plot will show the average velocity for each interval across all CSV files,
    # plotted against the RPM extracted from the filename.

    # Dictionary to store data: {interval_index: [(rpm, avg_velocity), ...]}
    aggregated_data = {} 

    for csv_file in csv_files:
        # Extract RPM from filename (assuming format like '..._XXXXrpm.csv')
        try:
            basename = os.path.basename(csv_file)
            rpm_str = basename.split('rpm')[0].split('_')[-1]
            rpm = int(rpm_str)
        except (IndexError, ValueError):
            print(f"Warning: Could not parse RPM from filename '{os.path.basename(csv_file)}'. Skipping for aggregate plot.")
            continue

        data = read_csv(csv_file)
        
        # Calculate average velocity for each column (interval)
        avg_velocities = np.mean(data, axis=0)

        for i, avg_v in enumerate(avg_velocities):
            if i not in aggregated_data:
                aggregated_data[i] = []
            aggregated_data[i].append((rpm, avg_v))

    # Create the scatter plot
    plt.figure(figsize=(12, 8))
    
    # The 'colors' colormap is already defined above and will be used here

    for interval_idx, points in sorted(aggregated_data.items()):
        # Unzip the points into separate lists for rpm and velocity
        rpms, velocities = zip(*points)
        
        # Plot the scatter points
        plt.scatter(rpms, velocities, label=f'v{interval_idx+1} Data', color=colors(interval_idx))
        
        # Calculate and plot the trendline (1st degree polynomial fit)
        if len(rpms) > 1: # Need at least 2 points for a line
            trend_coeffs = np.polyfit(rpms, velocities, 1)
            trend_line = np.poly1d(trend_coeffs)
            
            # Generate x-values for the trendline to span the range of RPMs
            rpm_range = np.linspace(min(rpms), max(rpms), 100)
            plt.plot(rpm_range, trend_line(rpm_range), linestyle='--', color=colors(interval_idx), label=f'v{interval_idx+1} Trend')

    plt.title('Average Interval Velocity vs. RPM')
    plt.xlabel('RPM')
    plt.ylabel('Average Velocity (m/s)')
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(SCRIPT_DIR, "plots", 'aggregate_velocity_vs_rpm.png'))
    plt.close()
    print("Aggregate scatter plot saved as 'aggregate_velocity_vs_rpm.png'")

