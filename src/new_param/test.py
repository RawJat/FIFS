import pandas as pd

# Load the dataset
file_path = r"D:\ED\FIFS\data\batting.csv"  # Update with your correct path
df = pd.read_csv(file_path)

# Print column names
print("Column Names in Dataset:")
print(df.columns)
