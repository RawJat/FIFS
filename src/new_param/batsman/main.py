import pandas as pd
from itertools import product


# --------------------------
# Helper function: Precompute latest row per grouping
# --------------------------
def get_latest_rows(df, group_cols):
    """Return a dictionary keyed by group tuple (or a single value)
    with the latest row (by Match Date) for that grouping."""
    df_sorted = df.sort_values("Match Date", ascending=False)
    latest = df_sorted.drop_duplicates(subset=group_cols)
    result = {}
    for _, row in latest.iterrows():
        # Create a key: if more than one grouping column, make a tuple
        key = tuple(row[col] for col in group_cols) if len(group_cols) > 1 else row[group_cols[0]]
        result[key] = row
    return result


# --------------------------
# Load full dataset and prepare data
# --------------------------
file_path = r"D:\ED\FIFS\data\batting.csv"  # Update path if needed
df = pd.read_csv(file_path)
df["Match Date"] = pd.to_datetime(df["Match Date"])
df["venue"] = df["venue"].str.strip()  # Remove extra spaces if any

# --------------------------
# Define required lists (provided)
# --------------------------
batters = [67773.0, 80247.0, 1174726.0, 80259.0, 67750.0, 90231.0, 57022.0, 61861.0, 84865.0, 87051.0, 46888.0,
           106332.0, 110065.0, 105215.0, 90143.0, 66398.0, 79159.0, 1670.0, 103762.0, 103792.0, 101340.0,
           58435.0, 54314.0, 72565.0, 1210488.0, 54222.0, 104260.0, 72093.0, 78285.0, 70472.0, 80817.0,
           59610.0, 101328.0, 50281.0, 104403.0, 66190.0, 80669.0, 70877.0, 47352.0, 102020.0, 47986.0,
           54674.0, 1210511.0, 70872.0, 56825.0, 102030.0, 61619.0, 91219.0, 102028.0, 66808.0, 91227.0,
           49427.0, 65672.0, 69920.0, 93785.0, 84027.0, 65029.0, 97293.0, 52656.0, 72379.0, 53271.0,
           59832.0, 56993.0, 72363.0, 71381.0, 82071.0, 101430.0, 67455.0, 70633.0, 1312645.0, 67609.0,
           60530.0, 63646.0, 49247.0, 86165.0, 48405.0, 71331.0, 95316.0, 98673.0, 49752.0, 75311.0,
           58772.0, 58403.0, 80639.0, 67190.0, 51088.0, 64402.0, 61802.0, 64947.0, 54369.0, 64864.0,
           959771.0, 89105.0, 59148.0, 67178.0, 107211.0, 76191.0, 70611.0, 56880.0, 72679.0, 65101.0,
           103878.0, 70577.0, 75215.0, 103402.0, 54018.0, 103399.0, 71839.0, 95855.0, 80653.0, 62853.0,
           70277.0, 594322.0, 53891.0, 61634.0, 67296.0, 50309.0, 66941.0, 73871.0, 55398.0, 70498.0,
           58408.0, 58190.0, 74137.0, 69697.0, 74351.0]

venues = ['Dubai International Cricket Stadium', 'National Stadium',
          'Gaddafi Stadium', 'Rawalpindi Cricket Stadium']

teams = ['Bangladesh', 'England', 'South Africa', 'New Zealand',
         'Australia', 'India', 'Pakistan', 'Afghanistan']

innings = [1, 2]

# --------------------------
# Precompute latest-match lookups for each grouping
# --------------------------
batter_latest = get_latest_rows(df, ["batter"])
bat_team_latest = get_latest_rows(df, ["bat_team"])
batter_vs_opp = get_latest_rows(df, ["batter", "opposition"])
bat_team_vs_opp = get_latest_rows(df, ["bat_team", "opposition"])
all_teams_vs_opp = get_latest_rows(df, ["opposition"])
batter_inn = get_latest_rows(df, ["batter", "innings"])
bat_team_inn = get_latest_rows(df, ["bat_team", "innings"])
all_teams_inn = get_latest_rows(df, ["innings"])
batter_venue = get_latest_rows(df, ["batter", "venue"])
bat_team_venue = get_latest_rows(df, ["bat_team", "venue"])
all_teams_venue = get_latest_rows(df, ["venue"])

# --------------------------
# Generate all valid combinations (7,000 rows)
# --------------------------
data_combinations = []
for batter in batters:
    # Determine batter's team from the full dataset (use mode)
    batter_rows = df[df["batter"] == batter]
    if batter_rows.empty:
        continue  # Skip if batter not found
    bat_team = batter_rows["bat_team"].mode().iloc[0]

    # Opponents: All teams except batter's own team
    opponents = [team for team in teams if team != bat_team]

    # Generate combinations of (opposition, venue, innings)
    for opposition, venue, inn in product(opponents, venues, innings):
        data_combinations.append((batter, bat_team, opposition, venue, inn))

generated_df = pd.DataFrame(data_combinations,
                            columns=["batter", "bat_team", "opposition", "venue", "innings"])


# --------------------------
# Helper: Safe lookup in a precomputed dictionary
# --------------------------
def lookup_value(lookup_dict, key, stat_col):
    row = lookup_dict.get(key, None)
    return row[stat_col] if row is not None and stat_col in row else None


# --------------------------
# List of statistic columns (as required in final dataset)
# --------------------------
stats_columns = [
    "batter_avg", "batter_rpm", "batter_sr", "batter_bpm",
    "batter_avg_last5", "batter_sr_last5", "batter_rpm_last5", "batter_bpm_last5",
    "bat_team_avg",
    "batter_avg_opp", "batter_sr_opp", "batter_rpm_opp", "batter_bpm_opp",
    "bat_team_avg_opp", "all_team_avg_opp",
    "batter_avg_inn", "batter_sr_inn", "batter_rpm_inn", "batter_bpm_inn",
    "bat_team_avg_inn", "all_team_avg_inn",
    "batter_avg_ven", "batter_sr_ven", "batter_rpm_ven", "batter_bpm_ven",
    "bat_team_avg_ven", "all_team_avg_ven"
]


# --------------------------
# Populate each generated row with latest match statistics
# --------------------------
def populate_row(row):
    batter = row["batter"]
    bat_team = row["bat_team"]
    opposition = row["opposition"]
    venue = row["venue"]
    inn = row["innings"]

    vals = {}

    # Batter-specific stats (latest match for batter)
    batter_data = batter_latest.get(batter, None)
    for stat in ["batter_avg", "batter_rpm", "batter_sr", "batter_bpm",
                 "batter_avg_last5", "batter_sr_last5", "batter_rpm_last5", "batter_bpm_last5"]:
        vals[stat] = batter_data[stat] if batter_data is not None else None

    # Batting team stats (latest match for bat_team)
    team_data = bat_team_latest.get(bat_team, None)
    vals["bat_team_avg"] = team_data["bat_team_avg"] if team_data is not None else None

    # Batter vs. Opposition stats (latest match for batter against opposition)
    for stat in ["batter_avg_opp", "batter_sr_opp", "batter_rpm_opp", "batter_bpm_opp"]:
        vals[stat] = lookup_value(batter_vs_opp, (batter, opposition), stat)

    # Bat team vs. Opposition stats (latest match for bat_team against opposition)
    vals["bat_team_avg_opp"] = lookup_value(bat_team_vs_opp, (bat_team, opposition), "bat_team_avg_opp")

    # All teams vs. Opposition stats (latest match for any team against opposition)
    vals["all_team_avg_opp"] = lookup_value(all_teams_vs_opp, opposition, "all_team_avg_opp")

    # Batter in Innings stats (latest match for batter in that innings)
    for stat in ["batter_avg_inn", "batter_sr_inn", "batter_rpm_inn", "batter_bpm_inn"]:
        vals[stat] = lookup_value(batter_inn, (batter, inn), stat)

    # Bat team in Innings stats (latest match for bat_team in that innings)
    vals["bat_team_avg_inn"] = lookup_value(bat_team_inn, (bat_team, inn), "bat_team_avg_inn")

    # All teams in Innings stats (latest match for any team in that innings)
    vals["all_team_avg_inn"] = lookup_value(all_teams_inn, inn, "all_team_avg_inn")

    # Batter at Venue stats (latest match for batter at that venue)
    for stat in ["batter_avg_ven", "batter_sr_ven", "batter_rpm_ven", "batter_bpm_ven"]:
        vals[stat] = lookup_value(batter_venue, (batter, venue), stat)

    # Bat team at Venue stats (latest match for bat_team at that venue)
    vals["bat_team_avg_ven"] = lookup_value(bat_team_venue, (bat_team, venue), "bat_team_avg_ven")

    # All teams at Venue stats (latest match for any team at that venue)
    vals["all_team_avg_ven"] = lookup_value(all_teams_venue, venue, "all_team_avg_ven")

    return pd.Series(vals)


# Apply the population function to each generated row
stats_df = generated_df.apply(populate_row, axis=1)

# Combine the basic columns with the statistics columns
final_df = pd.concat([generated_df, stats_df], axis=1)

# --------------------------
# Save the final dataset to CSV
# --------------------------
output_path = "generated_batting_data_v2.csv"
final_df.to_csv(output_path, index=False)
print(f"Dataset saved as {output_path}")
