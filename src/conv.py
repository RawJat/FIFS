import json
import csv
import os

# Folder containing JSON files
input_folder = r"D:\ED\FIFS\data\testfolder"
output_csv = "formatted_data.csv"

# Define CSV headers
headers = ["Match ID", "innings", "team", "batsman", "runs", "balls", "fours", "sixes", "strikeRate", "isOut",
           "wicketType", "fielders", "bowler"]

# Open the output CSV file
with open(output_csv, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(headers)  # Write headers

    # Loop through each JSON file in the folder
    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            match_id = filename.split(".")[0]  # Extract match ID from file name
            file_path = os.path.join(input_folder, filename)

            # Read JSON data
            with open(file_path, "r") as json_file:
                data = json.load(json_file)

            # Get player ID mapping
            player_registry = data["info"]["registry"]["people"]
            player_id_map = {name: pid for name, pid in player_registry.items()}  # Name → ID

            # Get all players from match info
            players_by_team = data["info"]["players"]

            # Process each innings
            for inning_index, inning in enumerate(data["innings"], start=1):
                team = inning["team"]

                # Track all players in the innings
                players_batted = set()
                player_stats = {}

                # Process ball-by-ball data
                for over in inning["overs"]:
                    for delivery in over["deliveries"]:
                        batter = delivery["batter"]
                        bowler = delivery["bowler"]
                        runs = delivery["runs"]["batter"]
                        is_out = "wicket" in delivery  # Check if the delivery resulted in a wicket
                        wicket_type = delivery["wicket"]["kind"] if is_out else "not out"

                        # Get fielder IDs if available (if delivery has fielders)
                        fielders = [player_id_map[f] for f in
                                    delivery["wicket"].get("fielders", [])] if is_out and "fielders" in delivery[
                            "wicket"] else []

                        # Convert names to IDs
                        batter_id = player_id_map.get(batter, batter)
                        bowler_id = player_id_map.get(bowler, bowler)

                        players_batted.add(batter_id)

                        # Store player stats
                        if batter_id not in player_stats:
                            player_stats[batter_id] = {
                                "runs": 0, "balls": 0, "fours": 0, "sixes": 0,
                                "isOut": is_out, "wicketType": wicket_type, "fielders": fielders, "bowler": bowler_id
                            }

                        player_stats[batter_id]["runs"] += runs
                        player_stats[batter_id]["balls"] += 1
                        if runs == 4:
                            player_stats[batter_id]["fours"] += 1
                        elif runs == 6:
                            player_stats[batter_id]["sixes"] += 1

                # Write data for each batsman who played
                for batter_id, stats in player_stats.items():
                    strike_rate = (stats["runs"] / stats["balls"]) * 100 if stats["balls"] > 0 else 0
                    # Write the fielders as an empty string if there are no fielders
                    fielders = ",".join(stats["fielders"]) if stats["fielders"] else ""
                    writer.writerow([
                        match_id, inning_index, team, batter_id, stats["runs"], stats["balls"],
                        stats["fours"], stats["sixes"], round(strike_rate, 2), stats["isOut"],
                        stats["wicketType"], fielders, stats["bowler"]
                    ])

                # Mark players who did not bat as "DNB"
                for player in players_by_team[team]:
                    player_id = player_id_map.get(player, player)
                    if player_id not in players_batted:
                        writer.writerow(
                            [match_id, inning_index, team, player_id, "", "", "", "", "", "False", "DNB", "", ""])

print(f"Data successfully saved to {output_csv}")
