import pandas as pd

# --- File Path ---
input_file = r'D:\ED\FIFS\src\v3_\24_25_batting_cardv3.csv'

# Load the CSV file into a DataFrame
df = pd.read_csv(input_file)

# Define the player-related columns to check
player_columns = ['batsman', 'bowler', 'fielders']

# Count and print missing values per column
for col in player_columns:
    missing_count = df[col].isna().sum()
    print(f"Missing {col} count: {missing_count}")

# Count and print the total missing player IDs across the specified columns
total_missing = df[player_columns].isna().sum().sum()
print(f"Total missing player IDs: {total_missing}")
