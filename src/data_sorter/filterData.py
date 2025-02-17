import os
import shutil
import pandas as pd

# Set source and destination folders
source_folder = "path/to/source_folder"
destination_folder = "path/to/destination_folder"

# Ensure the destination folder exists
os.makedirs(destination_folder, exist_ok=True)

# Define the cutoff date
cutoff_date = pd.Timestamp("2024-01-01")

# Loop through all files in the source folder
for filename in os.listdir(source_folder):
    if filename.endswith(".csv"):  # Process only CSV files
        match_id = filename[:-4]  # Extract match_id from filename
        csv_path = os.path.join(source_folder, filename)
        info_path = os.path.join(source_folder, f"{match_id}.info")

        try:
            # Read the first 5 rows of the CSV file
            df = pd.read_csv(csv_path, usecols=["start_date"], nrows=5, parse_dates=["start_date"])

            # Check if any start_date is on or after 2024-01-01
            if (df["start_date"] >= cutoff_date).any():
                # Copy both .csv and .info files to destination folder
                shutil.copy(csv_path, os.path.join(destination_folder, filename))
                if os.path.exists(info_path):  # Check if the .info file exists
                    shutil.copy(info_path, os.path.join(destination_folder, f"{match_id}.info"))

        except Exception as e:
            print(f"Error processing {filename}: {e}")

print("Filtering complete.")
