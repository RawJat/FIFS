import os
import pandas as pd

# --- File Paths ---
input_file = r'D:\ED\FIFS\src\v2_\24_25_batting_cardv2.csv'  # Input file with player IDs
mapping_file = r'D:\ED\FIFS\data\people.csv'  # File with identifier -> key_cricinfo mapping
output_file = r'D:\ED\FIFS\src\v3_\24_25_batting_cardv3.csv'  # Output file with replaced player IDs

# --- Load Data ---
df = pd.read_csv(input_file)
mapping_df = pd.read_csv(mapping_file)

# --- Create Mapping Dictionary (identifier -> key_cricinfo) ---
id_to_cricinfo = mapping_df.set_index('identifier')['key_cricinfo'].to_dict()

# --- Function to Map Player IDs ---
def map_player_id(player_id):
    if pd.isna(player_id):
        return None  # Keep null if already missing
    return id_to_cricinfo.get(player_id, None)  # Replace if found, else keep null

# --- Apply Mapping to Relevant Columns ---
columns_to_replace = ['batsman', 'bowler', 'fielders']
for col in columns_to_replace:
    df[col] = df[col].apply(map_player_id)

# --- Save Updated CSV ---
df.to_csv(output_file, index=False)

print(f"Updated file saved as: {output_file}")
