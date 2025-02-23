import pandas as pd
from difflib import SequenceMatcher

# ---------------------------
# Mapping and cleaning functions
# ---------------------------
team_mapping = {
    "BAN": "Bangladesh",
    "IND": "India",
    "ENG": "England",
    "SA": "South Africa",
    "NZ": "New Zealand",
    "AUS": "Australia",
    "PAK": "Pakistan",
    "AFG": "Afghanistan"
}


def map_team(abbrev):
    """Convert a team abbreviation (e.g., BAN) to its full name."""
    return team_mapping.get(abbrev.strip(), abbrev.strip())


def clean_venue(venue_str):
    """Clean the scraped venue string by taking the part before the comma."""
    return venue_str.split(",")[0].strip()


def load_generated_datasheet(file_path):
    """
    Load a generated datasheet (batting or bowling) into a DataFrame.
    Ensure key columns are cleaned (e.g. venue trimmed, innings as int).
    """
    df = pd.read_csv(file_path)
    df["venue"] = df["venue"].str.strip()
    df["innings"] = df["innings"].astype(int)
    return df


# ---------------------------
# Matching functions for batting and bowling
# ---------------------------
def match_scraped_to_generated_batting(scraped_df, gen_df):
    """
    For each row in the scraped DataFrame (with columns:
    Player Name, Team, Opponent, Venue, Innings),
    filter the batting datasheet (gen_df) to fetch the matching row based on:
      - Team (mapped) vs. bat_team,
      - Opponent (mapped) vs. opposition,
      - Venue (cleaned) vs. venue,
      - Innings (numeric) vs. innings.
    If the generated datasheet contains a 'batter_name' column,
    fuzzy matching is used on it.
    """
    matched_rows = []
    for idx, scraped_row in scraped_df.iterrows():
        team_full = map_team(scraped_row["Team"])
        opp_full = map_team(scraped_row["Opponent"])
        venue_clean = clean_venue(scraped_row["Venue"])
        innings_val = int(scraped_row["Innings"])
        player_name_scraped = scraped_row["Player Name"].strip()

        filtered = gen_df[
            (gen_df["bat_team"] == team_full) &
            (gen_df["opposition"] == opp_full) &
            (gen_df["venue"] == venue_clean) &
            (gen_df["innings"] == innings_val)
            ]

        if filtered.empty:
            print(f"Warning (Batting): No match found for '{player_name_scraped}' with parameters: "
                  f"Team={team_full}, Opponent={opp_full}, Venue={venue_clean}, Innings={innings_val}")
            continue

        # If available, use fuzzy matching on 'batter_name'
        if "batter_name" in filtered.columns:
            best_match = None
            best_ratio = 0
            for i, row in filtered.iterrows():
                ratio = SequenceMatcher(None, player_name_scraped.lower(), row["batter_name"].lower()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = row
            if best_match is not None and best_ratio > 0.8:
                matched_rows.append(best_match)
            else:
                print(f"Warning (Batting): No close fuzzy match for '{player_name_scraped}'")
        else:
            # If no batter_name available, and exactly one row exists, take that row.
            if len(filtered) == 1:
                matched_rows.append(filtered.iloc[0])
            else:
                print(
                    f"Warning (Batting): Multiple rows found for '{player_name_scraped}' and no 'batter_name' column to resolve.")

    return pd.DataFrame(matched_rows)


def match_scraped_to_generated_bowling(scraped_df, gen_df):
    """
    For each row in the scraped DataFrame (with columns:
    Player Name, Team, Opponent, Venue, Innings),
    filter the bowling datasheet (gen_df) to fetch the matching row based on:
      - Team (mapped) vs. bowl_team,
      - Opponent (mapped) vs. opposition,
      - Venue (cleaned) vs. venue,
      - Innings (numeric) vs. innings.
    If the generated datasheet contains a 'bowler_name' column,
    fuzzy matching is used on it.
    """
    matched_rows = []
    for idx, scraped_row in scraped_df.iterrows():
        team_full = map_team(scraped_row["Team"])
        opp_full = map_team(scraped_row["Opponent"])
        venue_clean = clean_venue(scraped_row["Venue"])
        innings_val = int(scraped_row["Innings"])
        player_name_scraped = scraped_row["Player Name"].strip()

        filtered = gen_df[
            (gen_df["bowl_team"] == team_full) &
            (gen_df["opposition"] == opp_full) &
            (gen_df["venue"] == venue_clean) &
            (gen_df["innings"] == innings_val)
            ]

        if filtered.empty:
            print(f"Warning (Bowling): No match found for '{player_name_scraped}' with parameters: "
                  f"Team={team_full}, Opponent={opp_full}, Venue={venue_clean}, Innings={innings_val}")
            continue

        # If available, use fuzzy matching on 'bowler_name'
        if "bowler_name" in filtered.columns:
            best_match = None
            best_ratio = 0
            for i, row in filtered.iterrows():
                ratio = SequenceMatcher(None, player_name_scraped.lower(), row["bowler_name"].lower()).ratio()
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = row
            if best_match is not None and best_ratio > 0.8:
                matched_rows.append(best_match)
            else:
                print(f"Warning (Bowling): No close fuzzy match for '{player_name_scraped}'")
        else:
            # If no bowler_name available, and exactly one row exists, take that row.
            if len(filtered) == 1:
                matched_rows.append(filtered.iloc[0])
            else:
                print(
                    f"Warning (Bowling): Multiple rows found for '{player_name_scraped}' and no 'bowler_name' column to resolve.")

    return pd.DataFrame(matched_rows)


# ---------------------------
# Main function
# ---------------------------
def main():
    # Load scraped match data (assumed saved as match_players.csv)
    scraped_df = pd.read_csv("today_match_details.csv")

    # Load the generated batting datasheet.
    batting_gen_file = r"D:\ED\FIFS\data\batting_generated.csv"
    batting_gen_df = load_generated_datasheet(batting_gen_file)

    # Load the generated bowling datasheet.
    bowling_gen_file = r"D:\ED\FIFS\data\bowling_generated.csv"
    bowling_gen_df = load_generated_datasheet(bowling_gen_file)

    # Match scraped data with batting generated data.
    matched_batting_df = match_scraped_to_generated_batting(scraped_df, batting_gen_df)
    if matched_batting_df.empty:
        print("No batting matches found between scraped data and generated datasheet.")
    else:
        matched_batting_df.to_csv("batting_test.csv", index=False)
        print("Matched batting data saved to 'batting_test.csv'.")

    # Match scraped data with bowling generated data.
    matched_bowling_df = match_scraped_to_generated_bowling(scraped_df, bowling_gen_df)
    if matched_bowling_df.empty:
        print("No bowling matches found between scraped data and generated datasheet.")
    else:
        matched_bowling_df.to_csv("bowling_test.csv", index=False)
        print("Matched bowling data saved to 'bowling_test.csv'.")


if __name__ == "__main__":
    main()
