import os
import pandas as pd
import numpy as np

# --- Configuration ---
input_folder = r'D:\ED\FIFS\data\testfolder'  # Folder where all match files are stored
output_folder = r'D:\ED\FIFS\src\v2_'       # Folder where the aggregated CSV will be saved
output_file = os.path.join(output_folder, '24_25_batting_cardv2.csv')

# Ensure output folder exists
os.makedirs(output_folder, exist_ok=True)

# --- List all files in the input folder ---
all_files = os.listdir(input_folder)

# Identify ball-by-ball CSV files (exclude info files)
ball_by_ball_files = [f for f in all_files if f.endswith('.csv') and '_info' not in f]

# List to hold aggregated DataFrames from each match
all_matches = []

for ball_file in ball_by_ball_files:
    # Infer match id from filename (e.g., "matchid1.csv" -> "matchid1")
    match_id = ball_file.replace('.csv', '')
    ball_file_path = os.path.join(input_folder, ball_file)

    # Read ball-by-ball data
    df = pd.read_csv(ball_file_path)

    # Column definitions
    innings_col = 'innings'
    team_col = 'batting_team'
    batsman_col = 'striker'
    bowler_col = 'bowler'
    runs_col = 'runs_off_bat'
    wicket_col = 'wicket_type'

    # Ensure runs are numeric
    df[runs_col] = pd.to_numeric(df[runs_col], errors='coerce').fillna(0)

    # Marking deliveries faced
    df['ball_faced'] = 1
    df['is_four'] = (df[runs_col] == 4).astype(int)
    df['is_six'] = (df[runs_col] == 6).astype(int)
    df['is_dismissal'] = df[wicket_col].notna() & (df[wicket_col] != '')

    # Aggregate batting data
    grouped = df.groupby([innings_col, team_col, batsman_col])
    agg_df = grouped.agg(
        runs=(runs_col, 'sum'),
        balls=('ball_faced', 'sum'),
        fours=('is_four', 'sum'),
        sixes=('is_six', 'sum')
    ).reset_index()

    agg_df['strikeRate'] = agg_df.apply(
        lambda row: round((row['runs'] / row['balls'] * 100), 2) if row['balls'] > 0 else 0,
        axis=1
    )

    # Process dismissal info
    def get_dismissal_info(sub_df):
        dismissal_rows = sub_df[sub_df['is_dismissal']]
        if not dismissal_rows.empty:
            first_dismissal = dismissal_rows.iloc[0]
            return pd.Series({
                'isOut': True,
                'wicketType': first_dismissal[wicket_col],
                'bowler': first_dismissal[bowler_col],
                'fielders': ''
            })
        else:
            return pd.Series({
                'isOut': False,
                'wicketType': 'not out',
                'bowler': '',
                'fielders': "['-']"
            })

    dismissal_info = grouped.apply(get_dismissal_info, include_groups=False).reset_index(drop=True)
    agg_df = pd.concat([agg_df, dismissal_info], axis=1)

    # Add Match ID column
    agg_df['Match ID'] = match_id

    # --- Load Player ID Mapping ---
    player_id_map = {}

    info_filename = f"{match_id}_info.csv"
    info_file_path = os.path.join(input_folder, info_filename)

    if os.path.exists(info_file_path):
        with open(info_file_path, 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 5 and parts[0] == 'info' and parts[1] == 'registry' and parts[2] == 'people':
                    player_name = parts[3]
                    player_id = parts[4]
                    player_id_map[player_name] = player_id

    # Replace names with player IDs
    agg_df[batsman_col] = agg_df[batsman_col].map(player_id_map)
    agg_df['bowler'] = agg_df['bowler'].map(player_id_map)

    # --- Process DNB (Did Not Bat) Players ---
    if os.path.exists(info_file_path):
        players = []
        with open(info_file_path, 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 4 and parts[0] == 'info' and parts[1] == 'player':
                    players.append({'team': parts[2], 'batsman': parts[3]})
        players_df = pd.DataFrame(players)

        teams_innings = agg_df[[innings_col, team_col]].drop_duplicates()
        for _, row in teams_innings.iterrows():
            inn = row[innings_col]
            team = row[team_col]
            team_players = players_df[players_df['team'] == team]['batsman'].tolist()
            batted_players = agg_df[(agg_df[innings_col] == inn) & (agg_df[team_col] == team)][batsman_col].dropna().tolist()
            dnb_players = [player for player in team_players if player not in batted_players]

            for player in dnb_players:
                dnb_record = {
                    'Match ID': match_id,
                    innings_col: inn,
                    team_col: team,
                    batsman_col: player_id_map.get(player, player),  # Replace name with ID if available
                    'runs': np.nan,
                    'balls': np.nan,
                    'fours': np.nan,
                    'sixes': np.nan,
                    'strikeRate': np.nan,
                    'isOut': False,
                    'wicketType': 'DNB',
                    'fielders': '',
                    'bowler': ''
                }
                agg_df = pd.concat([agg_df, pd.DataFrame([dnb_record])], ignore_index=True)

    # Reorder columns
    agg_df = agg_df[['Match ID', innings_col, team_col, batsman_col,
                     'runs', 'balls', 'fours', 'sixes', 'strikeRate',
                     'isOut', 'wicketType', 'fielders', 'bowler']]

    # Append aggregated data for this match to the master list
    all_matches.append(agg_df)

# --- Combine data from all matches ---
final_df = pd.concat(all_matches, ignore_index=True)

# Save final aggregated data to a CSV file
final_df.to_csv(output_file, index=False)
print("Aggregated match data saved to", output_file)
