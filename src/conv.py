import csv
import os

def process_match_file(match_file_path):
    """Process the match file and return formatted match details."""
    match_data = []
    with open(match_file_path, mode='r') as match_file:
        reader = csv.DictReader(match_file)
        batsman_data = {}

        for row in reader:
            try:
                # Check if necessary columns are present
                match_id = row['match_id']
                innings = row['innings']
                batting_team = row['batting_team']
                bowler = row['bowler']
                striker = row['striker']
                non_striker = row['non_striker']
                runs_off_bat = int(row['runs_off_bat'])
                extras = int(row['extras']) if row['extras'] else 0
                player_dismissed = row['player_dismissed']
                wicket_type = row['wicket_type']
                fielders = row.get('fielders', '')

                # Initialize batsman data
                for batsman in [striker, non_striker]:
                    if batsman not in batsman_data:
                        batsman_data[batsman] = {'runs': 0, 'balls': 0, 'fours': 0, 'sixes': 0, 'out': False}

                batsman_data[striker]['runs'] += runs_off_bat
                batsman_data[striker]['balls'] += 1
                if runs_off_bat == 4:
                    batsman_data[striker]['fours'] += 1
                if runs_off_bat == 6:
                    batsman_data[striker]['sixes'] += 1

                # Handle player dismissal
                if player_dismissed:
                    batsman_data[striker]['out'] = True
                    batsman_data[striker]['wicket_type'] = wicket_type
                    batsman_data[striker]['fielders'] = fielders

            except KeyError as e:
                # Handle missing columns gracefully
                print(f"Error processing row, missing column: {e}")
                continue  # Skip this row and move to the next

        # Format final match data
        for batsman, stats in batsman_data.items():
            strike_rate = "{:.2f}".format(stats['runs'] / stats['balls'] * 100) if stats['balls'] > 0 else "0.00"
            match_data.append({
                'match_id': match_id,
                'innings': innings,
                'batting_team': batting_team,
                'batsman': batsman,
                'runs': stats['runs'],
                'balls': stats['balls'],
                'fours': stats['fours'],
                'sixes': stats['sixes'],
                'strikeRate': strike_rate,
                'isOut': 'Yes' if stats.get('out', False) else 'No',
                'wicketType': stats.get('wicket_type', ''),
                'fielders': stats.get('fielders', ''),
                'bowler': bowler
            })

    return match_data

def process_files_in_folder(import_folder_path, export_folder_path, output_file):
    """Process all match files and store the data in a single CSV file in the export folder."""
    files = os.listdir(import_folder_path)
    match_files = [f for f in files if f.endswith('.csv') and not f.endswith('_info.csv')]

    all_match_data = []  # Store all match data

    for match_file in match_files:
        match_file_path = os.path.join(import_folder_path, match_file)

        # Process match data
        match_data = process_match_file(match_file_path)

        # Collect data
        all_match_data.extend(match_data)

    # Write all data to a single CSV file in the export folder
    if not os.path.exists(export_folder_path):
        os.makedirs(export_folder_path)

    output_path = os.path.join(export_folder_path, output_file)
    with open(output_path, mode='w', newline='') as output_file:
        fieldnames = ['match_id', 'innings', 'batting_team', 'batsman', 'runs', 'balls', 'fours', 'sixes',
                      'strikeRate', 'isOut', 'wicketType', 'fielders', 'bowler']
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_match_data)

    print(f"All match data has been successfully written to {output_path}")

def main():
    import_folder_path = r'D:\ED\FIFS\data\final_data'  # Path to input files
    export_folder_path = r'D:\ED\FIFS\data\output'  # Path to export folder (change as needed)
    output_file = "all_matches.csv"  # Output CSV file name
    process_files_in_folder(import_folder_path, export_folder_path, output_file)

if __name__ == '__main__':
    main()
