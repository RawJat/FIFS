import pandas as pd
import csv
import os
import re


def process_match_info(info_file):
    """Process match info file to get player lists for all teams."""
    teams = {}
    current_team = None

    with open(info_file, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 3:
                if row[1] == 'team':
                    # Initialize team in the dictionary if not present
                    current_team = row[2]
                    teams[current_team] = []
                elif row[1] == 'player' and row[2] in teams:
                    # Add player to their team
                    teams[row[2]].append(row[3])

    return teams


def process_batting_scorecard(ball_by_ball_file, match_info_file):
    """Process ball-by-ball data into batting scorecard format."""
    # Read ball-by-ball data
    df = pd.read_csv(ball_by_ball_file)

    # Get player lists from match info
    team_players = process_match_info(match_info_file)

    # Initialize batting statistics
    batting_stats = {}

    # Process each ball
    for _, ball in df.iterrows():
        striker = ball['striker']
        batting_team = ball['batting_team']

        # Initialize player stats if not exists
        if (batting_team, striker) not in batting_stats:
            batting_stats[(batting_team, striker)] = {
                'runs': 0,
                'balls': 0,
                'fours': 0,
                'sixes': 0,
                'isOut': False,
                'wicketType': '',
                'fielders': [],
                'bowler': '',
                'innings': ball['innings']
            }

        # Update statistics
        stats = batting_stats[(batting_team, striker)]
        runs = ball['runs_off_bat']
        stats['balls'] += 1
        stats['runs'] += runs

        if runs == 4:
            stats['fours'] += 1
        elif runs == 6:
            stats['sixes'] += 1

        # Check for wicket
        if pd.notna(ball['wicket_type']):
            stats['isOut'] = True
            stats['wicketType'] = ball['wicket_type']
            stats['bowler'] = ball['bowler']
            if pd.notna(ball['other_player_dismissed']):
                stats['fielders'].append(ball['other_player_dismissed'])

    # Create results DataFrame
    results = []

    # Get unique match date and venue for additional context
    match_date = df['start_date'].iloc[0]
    match_venue = df['venue'].iloc[0]

    # Process each team
    for team, players in team_players.items():
        for player in players:
            if (team, player) in batting_stats:
                stats = batting_stats[(team, player)]
                strike_rate = (stats['runs'] / stats['balls'] * 100) if stats['balls'] > 0 else 0

                results.append({
                    'MatchID': df['match_id'].iloc[0],
                    'Date': match_date,
                    'Venue': match_venue,
                    'innings': stats['innings'],
                    'team': team,
                    'batsman': player,
                    'runs': stats['runs'],
                    'balls': stats['balls'],
                    'fours': stats['fours'],
                    'sixes': stats['sixes'],
                    'strikeRate': round(strike_rate, 2),
                    'isOut': stats['isOut'],
                    'wicketType': stats['wicketType'] if stats['isOut'] else 'not out' if stats['balls'] > 0 else 'DNB',
                    'fielders': stats['fielders'],
                    'bowler': stats['bowler']
                })
            else:
                # Add DNB entry for players who didn't bat
                results.append({
                    'MatchID': df['match_id'].iloc[0],
                    'Date': match_date,
                    'Venue': match_venue,
                    'innings': 1 if team == df['batting_team'].iloc[0] else 2,
                    'team': team,
                    'batsman': player,
                    'runs': None,
                    'balls': None,
                    'fours': None,
                    'sixes': None,
                    'strikeRate': None,
                    'isOut': False,
                    'wicketType': 'DNB',
                    'fielders': [],
                    'bowler': ''
                })

    return pd.DataFrame(results)


def process_all_matches(folder_path):
    """Process all matches in the specified folder."""
    # Get all CSV files in the folder
    all_files = os.listdir(folder_path)

    # Find match files (excluding _info files)
    match_files = [f for f in all_files if f.endswith('.csv') and '_info' not in f]

    # Initialize list to store all scorecards
    all_scorecards = []

    # Process each match
    total_matches = len(match_files)
    for idx, match_file in enumerate(match_files, 1):
        try:
            # Extract match ID from filename
            match_id = match_file.replace('.csv', '')

            # Construct paths
            match_path = os.path.join(folder_path, match_file)
            info_path = os.path.join(folder_path, f"{match_id}_info.csv")

            # Process match if info file exists
            if os.path.exists(info_path):
                print(f"Processing match {idx}/{total_matches}: {match_id}")
                scorecard = process_batting_scorecard(match_path, info_path)
                all_scorecards.append(scorecard)
            else:
                print(f"Warning: Info file not found for match {match_id}")

        except Exception as e:
            print(f"Error processing match {match_id}: {str(e)}")
            continue

    # Combine all scorecards
    if all_scorecards:
        combined_scorecard = pd.concat(all_scorecards, ignore_index=True)
        return combined_scorecard
    else:
        return None


def main():
    # Get folder path from user
    folder_path = input("Enter the path to the folder containing match files: ").strip()

    # Verify folder exists
    if not os.path.exists(folder_path):
        print("Error: Folder not found!")
        return

    print("Starting to process matches...")
    combined_scorecard = process_all_matches(folder_path)

    if combined_scorecard is not None:
        # Save to CSV
        output_file = os.path.join(folder_path, "all_matches_scorecard.csv")
        combined_scorecard.to_csv(output_file, index=False)
        print(f"\nProcessing complete!")
        print(f"Total matches processed: {len(combined_scorecard['MatchID'].unique())}")
        print(f"Total innings processed: {len(combined_scorecard)}")
        print(f"Output saved to: {output_file}")
    else:
        print("No matches were processed successfully")


if __name__ == "__main__":
    main()