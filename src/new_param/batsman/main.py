import pandas as pd
from itertools import product


# --------------------------
# Helper function to compute latest row per group
# --------------------------
def get_latest_rows(df, group_cols):
    # Sort by "Match Date" descending, then drop duplicates for each group
    df_sorted = df.sort_values("Match Date", ascending=False)
    latest = df_sorted.drop_duplicates(subset=group_cols)
    result = {}
    for idx, row in latest.iterrows():
        # key is a tuple (if more than one grouping column) or a single value
        key = tuple(row[col] for col in group_cols) if len(group_cols) > 1 else row[group_cols[0]]
        result[key] = row
    return result


# --------------------------
# Load full dataset
# --------------------------
file_path = r"/data/batting.csv"  # Adjust path if needed
df = pd.read_csv(file_path)
df["Match Date"] = pd.to_datetime(df["Match Date"])
df["venue"] = df["venue"].str.strip()  # Clean extra spaces if any

# --------------------------
# Define required lists (given)
# --------------------------
batters = [80247.0, 1174726.0, 80259.0, 67750.0, 90231.0, 57022.0, 61861.0, 84865.0, 87051.0, 46888.0,
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

venues = ['Dubai International Cricket Stadium', 'National Stadium', 'Gaddafi Stadium', 'Rawalpindi Cricket Stadium']
teams = ['Bangladesh', 'England', 'South Africa', 'New Zealand', 'Australia', 'India', 'Pakistan', 'Afghanistan']
innings = [1, 2]

# --------------------------
# Precompute dictionaries for "latest" rows by various groupings.
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
# Generate all valid combinations for dataset (7000 rows)
# --------------------------
data_combinations = []
for batter in batters:
    # Determine bat_team for the batter from the full dataset (if available)
    batter_rows = df[df["batter"] == batter]
    if batter_rows.empty:
        continue  # Skip if batter not found
    bat_team = batter_rows["bat_team"].mode().iloc[0]
    # Opponents: all tournament teams except the batter's own team
    opponents = [team for team in teams if team != bat_team]
    for opposition, venue, inn in product(opponents, venues, innings):
        data_combinations.append((batter, bat_team, opposition, venue, inn))

generated_df = pd.DataFrame(data_combinations, columns=["batter", "bat_team", "opposition", "venue", "innings"])


# --------------------------
# Define a helper to safely get a value from a dictionary of rows.
# --------------------------
def lookup_value(dictionary, key, stat_col):
    # key might not be found; return None if not available.
    row = dictionary.get(key, None)
    return row[stat_col] if row is not None else None


# --------------------------
# List of statistics columns (as per input dataset, excluding Match ID and Match Date)
# --------------------------
stats_columns = [
    "batter_avg", "batter_rpm", "batter_sr", "batter_bpm",
    "batter_avg_last5", "batter_sr_last5", "batter_rpm_last5", "batter_bpm_last5",
    "batter_avg_opp", "batter_sr_opp", "batter_rpm_opp", "batter_bpm_opp",
    "bat_team_avg", "bat_team_avg_opp", "all_team_avg_opp",
    "batter_avg_inn", "batter_sr_inn", "batter_rpm_inn", "batter_bpm_inn",
    "bat_team_avg_inn", "all_team_avg_inn",
    "batter_avg_ven", "batter_sr_ven", "batter_rpm_ven", "batter_bpm_ven",
    "bat_team_avg_ven", "all_team_avg_ven"
]


# --------------------------
# Populate generated_df by looking up the latest stats from our precomputed dictionaries.
# --------------------------
def populate_row(row):
    batter = row["batter"]
    bat_team = row["bat_team"]
    opposition = row["opposition"]
    venue = row["venue"]
    inn = row["innings"]

    # Prepare a dictionary for the stats we need to fill
    values = {}

    # Batter-specific stats: latest match for batter regardless of other conditions
    batter_data = batter_latest.get(batter, None)
    for stat in ["batter_avg", "batter_rpm", "batter_sr", "batter_bpm",
                 "batter_avg_last5", "batter_sr_last5", "batter_rpm_last5", "batter_bpm_last5"]:
        values[stat] = batter_data[stat] if batter_data is not None else None

    # Batting team stats: latest match for bat_team regardless of other conditions
    team_data = bat_team_latest.get(bat_team, None)
    values["bat_team_avg"] = team_data["bat_team_avg"] if team_data is not None else None

    # Batter vs. Opposition stats
    values["batter_avg_opp"] = lookup_value(batter_vs_opp, (batter, opposition), "batter_avg_opp")
    values["batter_sr_opp"] = lookup_value(batter_vs_opp, (batter, opposition), "batter_sr_opp")
    values["batter_rpm_opp"] = lookup_value(batter_vs_opp, (batter, opposition), "batter_rpm_opp")
    values["batter_bpm_opp"] = lookup_value(batter_vs_opp, (batter, opposition), "batter_bpm_opp")

    # Batting team vs. Opposition stats
    values["bat_team_avg_opp"] = lookup_value(bat_team_vs_opp, (bat_team, opposition), "bat_team_avg_opp")

    # All teams vs. Opposition stats
    values["all_team_avg_opp"] = lookup_value(all_teams_vs_opp, opposition, "all_team_avg_opp")

    # Batter in Innings stats
    values["batter_avg_inn"] = lookup_value(batter_inn, (batter, inn), "batter_avg_inn")
    values["batter_sr_inn"] = lookup_value(batter_inn, (batter, inn), "batter_sr_inn")
    values["batter_rpm_inn"] = lookup_value(batter_inn, (batter, inn), "batter_rpm_inn")
    values["batter_bpm_inn"] = lookup_value(batter_inn, (batter, inn), "batter_bpm_inn")

    # Batting team in Innings stats
    values["bat_team_avg_inn"] = lookup_value(bat_team_inn, (bat_team, inn), "bat_team_avg_inn")

    # All teams in Innings stats
    values["all_team_avg_inn"] = lookup_value(all_teams_inn, inn, "all_team_avg_inn")

    # Batter at Venue stats
    values["batter_avg_ven"] = lookup_value(batter_venue, (batter, venue), "batter_avg_ven")
    values["batter_sr_ven"] = lookup_value(batter_venue, (batter, venue), "batter_sr_ven")
    values["batter_rpm_ven"] = lookup_value(batter_venue, (batter, venue), "batter_rpm_ven")
    values["batter_bpm_ven"] = lookup_value(batter_venue, (batter, venue), "batter_bpm_ven")

    # Batting team at Venue stats
    values["bat_team_avg_ven"] = lookup_value(bat_team_venue, (bat_team, venue), "bat_team_avg_ven")

    # All teams at Venue stats
    values["all_team_avg_ven"] = lookup_value(all_teams_venue, venue, "all_team_avg_ven")

    return pd.Series(values)


# Apply the population function for each generated row
stats_df = generated_df.apply(populate_row, axis=1)

# Combine the basic generated columns with the stats columns
final_df = pd.concat([generated_df, stats_df], axis=1)

# --------------------------
# Save the generated dataset
# --------------------------
output_path = "worked_ds.csv"
final_df.to_csv(output_path, index=False)
print(f"Dataset saved as {output_path}")
