import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime, timezone
from difflib import SequenceMatcher
import pandas as pd

SERIES_SCHEDULE_URL = "https://www.cricbuzz.com/cricket-series/9325/icc-champions-trophy-2025/matches"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def similarity(a, b):
    """Return a similarity ratio between two strings (case-insensitive)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def get_match_urls():
    """Fetch all ICC Champions Trophy 2025 match URLs."""
    response = requests.get(SERIES_SCHEDULE_URL, headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Error fetching fixtures page: {response.status_code}")
        return []
    soup = BeautifulSoup(response.text, "html.parser")
    match_links = []
    seen_match_ids = set()
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "/live-cricket-scores/" in href and "icc-champions-trophy" in href:
            parts = href.split("/")
            if len(parts) >= 3:
                match_id = parts[-2]
                match_name = parts[-1]
                match_url = f"https://www.cricbuzz.com/cricket-match-facts/{match_id}/{match_name}"
                if match_id not in seen_match_ids:
                    seen_match_ids.add(match_id)
                    match_links.append(match_url)
    print(f"🔗 Found {len(match_links)} unique ICC Champions Trophy Match Facts URLs\n")
    return match_links


def extract_match_date(soup):
    """Extract match date from the match facts page."""
    try:
        date_tag = soup.find("span", class_="schedule-date")
        if date_tag and "timestamp" in date_tag.attrs:
            timestamp = int(date_tag["timestamp"])
            parsed_date = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
            return parsed_date.strftime("%d %b")  # e.g., '20 Feb'
        return "Unknown"
    except Exception as e:
        print(f"⚠️ Error extracting match date: {e}")
        return "Unknown"


def extract_playing_xi(soup):
    """Extract the playing XI for each team from the page."""
    match_info_sections = soup.select("div.cb-col.cb-col-73.cb-mat-fct-itm")
    player_names = []
    for section in match_info_sections:
        text = section.get_text(strip=True)
        if "," in text and len(text.split(",")) >= 8:
            player_names.append(text)
    if len(player_names) < 2:
        return [], []
    team1_players = [player.strip() for player in player_names[0].split(",")[:11]]
    team2_players = [player.strip() for player in player_names[1].split(",")[:11]]
    return team1_players, team2_players


def extract_match_details(match_url):
    """Extract match date, teams, venue, toss info, and playing XI details."""
    response = requests.get(match_url, headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Error fetching match page: {response.status_code}")
        return None, []
    soup = BeautifulSoup(response.text, "html.parser")
    match_data = []
    match_date = extract_match_date(soup)

    fact_sections = soup.select("div.cb-col.cb-col-73.cb-mat-fct-itm")
    venue = fact_sections[4].get_text(strip=True) if len(fact_sections) > 4 else "Unknown"
    toss_info = fact_sections[2].get_text(strip=True) if len(fact_sections) > 2 else "Unknown"

    teams_info = fact_sections[0].get_text(strip=True)
    teams = teams_info.split(" vs ")
    if len(teams) >= 2:
        team1_name = teams[0].strip().split(",")[0]
        team2_name = teams[1].strip().split(",")[0]
    else:
        print(f"⚠️ Error extracting team names for {match_url}")
        return match_date, []

    team1_players, team2_players = extract_playing_xi(soup)
    if not team1_players or not team2_players:
        print(f"❌ No players found for {match_date} despite a date match!")
        return match_date, []

    # Determine innings based on toss info.
    team1_innings, team2_innings = 1, 2  # default assumption: team1 bats first
    if "won the toss" in toss_info:
        toss_team_raw = toss_info.split(" won the toss")[0].strip()
        decision = ""
        if " elected to " in toss_info:
            decision = toss_info.split(" won the toss and elected to ")[1].strip().lower()
        elif " opt to " in toss_info:
            decision = toss_info.split(" won the toss and opt to ")[1].strip().lower()
        ratio1 = similarity(toss_team_raw, team1_name)
        ratio2 = similarity(toss_team_raw, team2_name)
        toss_winner = team1_name if ratio1 >= ratio2 else team2_name
        if decision.startswith("bat"):
            batting_team = toss_winner
        elif decision.startswith("bowl"):
            batting_team = team2_name if toss_winner == team1_name else team1_name
        else:
            batting_team = team1_name
        team1_innings = 1 if batting_team == team1_name else 2
        team2_innings = 1 if batting_team == team2_name else 2
    else:
        print(f"⚠️ Toss info not found or unexpected: '{toss_info}'. Defaulting innings.")

    # Build rows for both teams.
    for player in team1_players:
        match_data.append([
            player,
            team1_name,
            team2_name,
            venue,
            toss_info,
            team1_innings
        ])
    for player in team2_players:
        match_data.append([
            player,
            team2_name,
            team1_name,
            venue,
            toss_info,
            team2_innings
        ])

    return match_date, match_data


def save_to_csv(data, filename="match_players.csv"):
    """Save scraped match data to CSV."""
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Player Name", "Team", "Opponent", "Venue", "Toss Info", "Innings"])
        writer.writerows(data)


# ------------- New Integration Functions ------------- #

# Mapping for team abbreviations to full names.
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


def load_generated_datasheet(file_path="generated_batting_data.csv"):
    """Load the generated datasheet (e.g., batting data) into a DataFrame."""
    df = pd.read_csv(file_path)
    df["venue"] = df["venue"].str.strip()
    # Ensure the key columns are of the correct type (e.g., innings as int)
    df["innings"] = df["innings"].astype(int)
    return df


def match_scraped_to_generated(scraped_df, gen_df):
    """
    For each row in the scraped DataFrame (with columns: Player Name, Team, Opponent, Venue, Innings),
    filter the generated datasheet (gen_df) to fetch the matching row.
    The matching is done on:
      - Team (mapped to full name) vs. bat_team
      - Opponent (mapped) vs. opposition
      - Venue (cleaned) vs. venue
      - Innings (numeric) vs. innings
    Optionally, if the generated datasheet has a "batter_name" column, fuzzy matching is used.
    """
    matched_rows = []
    for idx, scraped_row in scraped_df.iterrows():
        team_full = map_team(scraped_row["Team"])
        opp_full = map_team(scraped_row["Opponent"])
        venue_clean = clean_venue(scraped_row["Venue"])
        innings_val = int(scraped_row["Innings"])
        player_name_scraped = scraped_row["Player Name"].strip()

        # Filter by team, opponent, venue, and innings.
        filtered = gen_df[
            (gen_df["bat_team"] == team_full) &
            (gen_df["opposition"] == opp_full) &
            (gen_df["venue"] == venue_clean) &
            (gen_df["innings"] == innings_val)
            ]
        if filtered.empty:
            print(
                f"Warning: No match found for '{player_name_scraped}' with parameters: Team={team_full}, Opponent={opp_full}, Venue={venue_clean}, Innings={innings_val}")
            continue

        # If the generated datasheet has a batter_name column, use fuzzy matching.
        if "batter_name" in filtered.columns:
            best_match = None
            best_ratio = 0
            for i, row in filtered.iterrows():
                ratio = similarity(player_name_scraped, row["batter_name"])
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_match = row
            if best_match is not None and best_ratio > 0.8:  # threshold can be adjusted
                matched_rows.append(best_match)
            else:
                print(f"Warning: No close match for '{player_name_scraped}' in filtered rows.")
        else:
            # If no batter_name is available and exactly one row exists, take that.
            if len(filtered) == 1:
                matched_rows.append(filtered.iloc[0])
            else:
                print(
                    f"Warning: Multiple rows found for '{player_name_scraped}' but no 'batter_name' column to resolve.")
    return pd.DataFrame(matched_rows)


# ---------------------------
# Main function integrating scraped and generated data
# ---------------------------
def main():
    # 1. Scrape match details and save the playing XI.
    user_date = input("Enter match date (e.g., '19 Feb'): ")
    match_urls = get_match_urls()
    scraped_match_data = None
    for match_url in match_urls:
        match_date, match_data = extract_match_details(match_url)
        print(f"🔍 Checking {match_url} | Extracted Date: '{match_date}' | User Input: '{user_date}'")
        if match_data and match_date.lower() == user_date.lower():
            print(f"✅ Match found on {match_date}: {match_url}")
            save_to_csv(match_data, filename="match_players.csv")
            scraped_match_data = pd.read_csv("match_players.csv")
            break
    if scraped_match_data is None or scraped_match_data.empty:
        print("❌ No match found for the given date or scraped data is empty.")
        return

    # 2. Load the generated datasheet (e.g., batting data)
    gen_df = load_generated_datasheet(r"D:\ED\FIFS\data\batting_generated.csv")

    # 3. Match scraped rows with generated datasheet rows.
    matched_df = match_scraped_to_generated(scraped_match_data, gen_df)

    # 4. Save the matched data to a CSV.
    matched_df.to_csv("matched_batting_data.csv", index=False)
    print("✅ Matched data saved to 'matched_batting_data.csv'")


if __name__ == "__main__":
    main()
