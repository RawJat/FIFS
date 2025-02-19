import pandas as pd

# --- File Paths ---
input_file = r'D:\ED\FIFS\src\v3_\24_25_batting_cardv3.csv'
output_file = r'D:\ED\FIFS\src\v3_\missing_player_ids.csv'

# Load the CSV file into a DataFrame
df = pd.read_csv(input_file)

# Create a new column 'LineNumber' based on the original row numbers (starting at 1)
df['LineNumber'] = df.index + 1

# Move 'LineNumber' to the very beginning of the DataFrame
cols = df.columns.tolist()
cols = ['LineNumber'] + [col for col in cols if col != 'LineNumber']
df = df[cols]

# Define the player-related columns to check for missing IDs
player_columns = ['batsman', 'bowler', 'fielders']

# Filter rows where any of the specified player columns are missing (NaN)
missing_rows = df[df[player_columns].isna().any(axis=1)]

# Write the filtered rows to a new CSV file (preserving the original line numbers)
missing_rows.to_csv(output_file, index=False)

print(f"Rows with missing player IDs have been saved to: {output_file}")
