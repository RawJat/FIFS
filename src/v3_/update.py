import pandas as pd

# --- File Paths ---
input_file = r'D:\ED\FIFS\src\v3_\24_25_batting_cardv3.csv'
output_file = r'D:\ED\FIFS\src\v3_\batting_card_25.csv'

# Load the CSV file into a DataFrame
df = pd.read_csv(input_file)

# Define a function to remove trailing ".0" from a value
def remove_trailing_decimal(val):
    # If the value is missing, return it as is
    if pd.isna(val):
        return val
    # Convert the value to string
    s = str(val)
    # Remove trailing ".0" if it exists
    if s.endswith('.0'):
        return s[:-2]
    return s

# List the player-related columns to be cleaned
player_columns = ['batsman', 'bowler', 'fielders']

# Apply the cleaning function to each player-related column (if present)
for col in player_columns:
    if col in df.columns:
        df[col] = df[col].apply(remove_trailing_decimal)

# Save the cleaned DataFrame to a new CSV file
df.to_csv(output_file, index=False)
print("Cleaned file saved as:", output_file)
