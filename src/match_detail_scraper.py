import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime, timezone
from difflib import SequenceMatcher

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
    # Look for sections containing comma-separated names (likely team lists)
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
    """Extract match date, teams, venue, toss info, and determine innings based on toss decision."""
    response = requests.get(match_url, headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Error fetching match page: {response.status_code}")
        return None, []
    soup = BeautifulSoup(response.text, "html.parser")
    match_data = []
    match_date = extract_match_date(soup)

    # Extract fact sections for venue, toss info, and team header.
    fact_sections = soup.select("div.cb-col.cb-col-73.cb-mat-fct-itm")
    venue = fact_sections[4].get_text(strip=True) if len(fact_sections) > 4 else "Unknown"
    toss_info = fact_sections[2].get_text(strip=True) if len(fact_sections) > 2 else "Unknown"

    # Extract team names from the header and clean up extra data by splitting on comma.
    teams_info = fact_sections[0].get_text(strip=True)
    teams = teams_info.split(" vs ")
    if len(teams) >= 2:
        team1_name = teams[0].strip().split(",")[0]
        team2_name = teams[1].strip().split(",")[0]
    else:
        print(f"⚠️ Error extracting team names for {match_url}")
        return match_date, []

    # Extract playing XI.
    team1_players, team2_players = extract_playing_xi(soup)
    if not team1_players or not team2_players:
        print(f"❌ No players found for {match_date} despite a date match!")
        return match_date, []

    # Determine which team bats first using toss info.
    # Expected toss info format: "<Team> won the toss and opt(elected to) <decision>"
    team1_innings, team2_innings = 1, 2  # default: assume team1 bats first
    if "won the toss" in toss_info:
        toss_team_raw = toss_info.split(" won the toss")[0].strip()
        decision = ""
        if " elected to " in toss_info:
            decision = toss_info.split(" won the toss and elected to ")[1].strip().lower()
        elif " opt to " in toss_info:
            decision = toss_info.split(" won the toss and opt to ")[1].strip().lower()

        # Use fuzzy matching to decide which team (from the header) best matches the toss winner.
        ratio1 = similarity(toss_team_raw, team1_name)
        ratio2 = similarity(toss_team_raw, team2_name)
        toss_winner = team1_name if ratio1 >= ratio2 else team2_name

        # If decision is to bat, toss winner bats first; if they opt to bowl, the opposition bats first.
        if decision.startswith("bat"):
            batting_team = toss_winner
        elif decision.startswith("bowl"):
            batting_team = team2_name if toss_winner == team1_name else team1_name
        else:
            batting_team = team1_name  # fallback

        team1_innings = 1 if batting_team == team1_name else 2
        team2_innings = 1 if batting_team == team2_name else 2
    else:
        print(f"⚠️ Toss info not found or unexpected: '{toss_info}'. Defaulting innings.")

    # Build CSV rows for both teams.
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
    """Save extracted match data to a CSV file."""
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Player Name", "Team", "Opponent", "Venue", "Toss Info", "Innings"])
        writer.writerows(data)


def main():
    user_date = input("Enter match date (e.g., '19 Feb'): ")
    match_urls = get_match_urls()
    for match_url in match_urls:
        match_date, match_data = extract_match_details(match_url)
        print(f"🔍 Checking {match_url} | Extracted Date: '{match_date}' | User Input: '{user_date}'")
        if match_data and match_date.lower() == user_date.lower():
            print(f"✅ Match found on {match_date}: {match_url}")
            save_to_csv(match_data)
            print("✅ CSV file saved successfully: match_players.csv")
            return
    print("❌ No match found for the given date.")


if __name__ == "__main__":
    main()
