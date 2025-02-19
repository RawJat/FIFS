import os
import pandas as pd
import numpy as np

# --- Configuration ---
input_folder = r'D:\ED\FIFS\data\final_data'  # Folder where all match files are stored
output_folder = r'D:\ED\FIFS\src\v1_'       # Folder where the aggregated CSV will be saved
output_file = os.path.join(output_folder, '24_25_batting_cardv1.csv')

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

    # --- Column assumptions ---
    # 'innings'      : innings number
    # 'batting_team': team batting in the delivery
    # 'striker'     : batsman facing the ball
    # 'bowler'      : bowler's name
    # 'runs_off_bat': runs scored off the bat
    # 'wicket_type' : non-empty if a wicket fell
    innings_col = 'innings'
    team_col = 'batting_team'
    batsman_col = 'striker' 
    bowler_col = 'bowler'
    runs_col = 'runs_off_bat'
    wicket_col = 'wicket_type'

    # Ensure runs are numeric
    df[runs_col] = pd.to_numeric(df[runs_col], errors='coerce').fillna(0)

    # Each row is one delivery faced
    df['ball_faced'] = 1

    # Identify boundaries for fours and sixes
    df['is_four'] = (df[runs_col] == 4).astype(int)
    df['is_six'] = (df[runs_col] == 6).astype(int)

    # Mark dismissal if wicket_type is not empty
    df['is_dismissal'] = df[wicket_col].notna() & (df[wicket_col] != '')

    # --- Aggregate batting data by innings, team, and batsman ---
    grouped = df.groupby([innings_col, team_col, batsman_col])
    agg_df = grouped.agg(
        runs=(runs_col, 'sum'),
        balls=('ball_faced', 'sum'),
        fours=('is_four', 'sum'),
        sixes=('is_six', 'sum')
    ).reset_index()

    # Calculate strike rate = (runs/balls)*100 if balls > 0
    agg_df['strikeRate'] = agg_df.apply(
        lambda row: round((row['runs'] / row['balls'] * 100), 2) if row['balls'] > 0 else 0,
        axis=1
    )

    # --- Determine dismissal details per batsman group ---
    def get_dismissal_info(sub_df):
        dismissal_rows = sub_df[sub_df['is_dismissal']]
        if not dismissal_rows.empty:
            first_dismissal = dismissal_rows.iloc[0]
            return pd.Series({
                'isOut': True,
                'wicketType': first_dismissal[wicket_col],
                'bowler': first_dismissal[bowler_col],
                'fielders': ''  # Adjust if you have fielders information
            })
        else:
            return pd.Series({
                'isOut': False,
                'wicketType': 'not out',
                'bowler': '',
                'fielders': "['-']"  # Indicates no fielders involved
            })

    # Use include_groups=False to silence the deprecation warning
    dismissal_info = grouped.apply(get_dismissal_info, include_groups=False).reset_index(drop=True)
    agg_df = pd.concat([agg_df, dismissal_info], axis=1)

    # Add Match ID column
    agg_df['Match ID'] = match_id

    # Reorder columns to match the desired format:
    # Match ID, innings, team, batsman, runs, balls, fours, sixes, strikeRate, isOut, wicketType, fielders, bowler
    agg_df = agg_df[['Match ID', innings_col, team_col, batsman_col,
                     'runs', 'balls', 'fours', 'sixes', 'strikeRate',
                     'isOut', 'wicketType', 'fielders', 'bowler']]

    # --- Process DNB (Did Not Bat) Players ---
    # Read the corresponding info file manually to parse the player list.
    # Example lines in the info file:
    # info,player,West Indies,A Athanaze
    # info,player,Australia,TM Head
    info_filename = f"{match_id}_info.csv"
    info_file_path = os.path.join(input_folder, info_filename)

    if os.path.exists(info_file_path):
        players = []
        with open(info_file_path, 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                # Check for lines that have at least 4 values and match the pattern "info,player,team,player"
                if len(parts) >= 4 and parts[0] == 'info' and parts[1] == 'player':
                    players.append({'team': parts[2], 'batsman': parts[3]})
        players_df = pd.DataFrame(players)

        # For each combination of innings and team in this match, add DNB records for players who did not bat.
        teams_innings = agg_df[[innings_col, team_col]].drop_duplicates()
        for _, row in teams_innings.iterrows():
            inn = row[innings_col]
            team = row[team_col]
            # Get all players for this team from the info file
            team_players = players_df[players_df['team'] == team]['batsman'].tolist()
            # Get players who actually batted in this innings for this team
            batted_players = agg_df[(agg_df[innings_col] == inn) & (agg_df[team_col] == team)][batsman_col].tolist()
            dnb_players = [player for player in team_players if player not in batted_players]

            for player in dnb_players:
                dnb_record = {
                    'Match ID': match_id,
                    innings_col: inn,
                    team_col: team,
                    batsman_col: player,
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
                # Replace .append with pd.concat
                agg_df = pd.concat([agg_df, pd.DataFrame([dnb_record])], ignore_index=True)

    # Append aggregated data for this match to the master list
    all_matches.append(agg_df)

# --- Combine data from all matches into a single DataFrame ---
final_df = pd.concat(all_matches, ignore_index=True)

# Save the final aggregated data to a CSV file in the output folder
final_df.to_csv(output_file, index=False)
print("Aggregated match data saved to", output_file)
