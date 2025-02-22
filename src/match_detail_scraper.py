import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime, timezone

# Base URL for upcoming international series
SERIES_SCHEDULE_URL = "https://www.cricbuzz.com/cricket-series/9325/icc-champions-trophy-2025/matches"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_match_urls():
    """Fetch all ICC Champions Trophy 2025 match URLs correctly."""
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
    """Extracts match date from the match facts page."""
    try:
        date_tag = soup.find("span", class_="schedule-date")
        if date_tag and "timestamp" in date_tag.attrs:
            timestamp = int(date_tag["timestamp"])
            parsed_date = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
            return parsed_date.strftime("%d %b")  # Convert to '20 Feb' format
        return "Unknown"
    except Exception as e:
        print(f"⚠️ Error extracting match date: {e}")
        return "Unknown"

def extract_playing_xi(soup):
    """Extracts Playing XI correctly from the page."""
    match_info_sections = soup.select("div.cb-col.cb-col-73.cb-mat-fct-itm")
    player_names = []

    # Extract only lines with comma-separated names (avoiding venue, toss info, etc.)
    for section in match_info_sections:
        text = section.get_text(strip=True)
        if "," in text and len(text.split(",")) >= 8:  # Likely a team list
            player_names.append(text)

    if len(player_names) < 2:
        return [], []

    # Extract both teams' Playing XI (First 11 names per team)
    team1_players = player_names[0].split(",")[:11]
    team2_players = player_names[1].split(",")[:11]

    return team1_players, team2_players

def extract_match_details(match_url):
    """Extracts match date, playing XI, teams, venue, toss, and innings from a match URL."""
    response = requests.get(match_url, headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Error fetching match page: {response.status_code}")
        return None, []
    
    soup = BeautifulSoup(response.text, "html.parser")
    match_data = []
    
    # Extract match date
    match_date = extract_match_date(soup)

    # Extract venue
    fact_sections = soup.select("div.cb-col.cb-col-73.cb-mat-fct-itm")
    venue = fact_sections[4].get_text(strip=True) if len(fact_sections) > 4 else "Unknown"

    # Extract toss info
    toss_info = fact_sections[2].get_text(strip=True) if len(fact_sections) > 2 else "Unknown"

    # Extract team names
    if len(fact_sections) > 0:
        teams_info = fact_sections[0].get_text(strip=True).split(",")[0]  # Extracts "BAN vs IND"
        teams = teams_info.split(" vs ") if " vs " in teams_info else []
    else:
        teams = []

    if len(teams) >= 2:
        team1_name, team2_name = teams[0], teams[1]
    else:
        print(f"⚠️ Error extracting team names for {match_url}")
        return match_date, []

    # Extract playing XI
    team1_players, team2_players = extract_playing_xi(soup)

    if not team1_players or not team2_players:
        print(f"❌ No players found for {match_date} despite a date match!")
        return match_date, []

    # Determine innings based on toss decision
    toss_winner = toss_info.split(" won the toss and opt to ")
    if len(toss_winner) == 2:
        toss_team, decision = toss_winner[0], toss_winner[1]

        if toss_team == team1_name:
            bat_first_team = team1_name if decision == "bat" else team2_name
        else:
            bat_first_team = team2_name if decision == "bat" else team1_name

        team1_innings = 1 if bat_first_team == team1_name else 2
        team2_innings = 1 if bat_first_team == team2_name else 2
    else:
        # Default to assuming team1 bats first if toss extraction fails
        team1_innings, team2_innings = 1, 2

    # Format match data
    for i, player in enumerate(team1_players):
        match_data.append([
            player,
            team1_name,
            team2_name,
            venue,
            toss_info,
            team1_innings
        ])

    for i, player in enumerate(team2_players):
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
    """Saves extracted data to a CSV file."""
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
        print(f"🔍 Comparing '{match_date.lower()}' == '{user_date.lower()}' ? => {match_date.lower() == user_date.lower()}")

        if match_data and match_date.lower() == user_date.lower():
            print(f"✅ Match found on {match_date}: {match_url}")
            save_to_csv(match_data)
            print("✅ CSV file saved successfully: match_players.csv")
            return

    print("❌ No match found for the given date.")

if __name__ == "__main__":
    main()
