import pandas as pd

# --- File Paths ---
input_file = r'D:\ED\FIFS\src\v3_\batting_card_25.csv'
output_file = r'D:\ED\FIFS\src\v3_\missing_player_ids_with_exceptions.csv'

# Load the CSV file into a DataFrame
df = pd.read_csv(input_file)

# Add a "LineNumber" column reflecting the original row numbers (starting at 1)
df['LineNumber'] = df.index + 1

# Move "LineNumber" to the very beginning of the DataFrame
cols = df.columns.tolist()
cols = ['LineNumber'] + [col for col in cols if col != 'LineNumber']
df = df[cols]


# Define a function to flag rows with missing required player IDs
def flag_missing(row):
    # Convert wicketType to lowercase string for comparison
    wt = str(row['wicketType']).strip().lower()

    # For DNB or not out, we require a batsman ID; missing bowler is allowed.
    if wt in ['dnb', 'not out']:
        if pd.isna(row['batsman']):
            return True  # Missing batsman is critical
        else:
            return False  # Otherwise, it's fine
    else:
        # For dismissed players, both batsman and bowler must be present.
        if pd.isna(row['batsman']) or pd.isna(row['bowler']):
            return True
        else:
            return False


# Apply the flagging function across the DataFrame rows
# (Note: We don't check "fielders" because missing fielders is acceptable.)
flagged_rows = df[df.apply(flag_missing, axis=1)]

# Write the flagged rows (with the original "LineNumber") to a new CSV file
flagged_rows.to_csv(output_file, index=False)

print(f"Flagged rows with missing required player IDs have been saved to: {output_file}")
