import pandas as pd
from itertools import product


# ----------------------------------------
# Helper: Precompute latest row per grouping
# ----------------------------------------
def get_latest_rows(df, group_cols):
    """
    For the given grouping (e.g. ["bowler", "venue"]), sort the dataframe by Match Date descending,
    then drop duplicates to keep the latest row per group.
    Returns a dictionary mapping each group key (tuple if multiple columns) to the row.
    """
    df_sorted = df.sort_values("Match Date", ascending=False)
    latest = df_sorted.drop_duplicates(subset=group_cols)
    result = {}
    for _, row in latest.iterrows():
        key = tuple(row[col] for col in group_cols) if len(group_cols) > 1 else row[group_cols[0]]
        result[key] = row
    return result


# ----------------------------------------
# Load the full bowling dataset
# ----------------------------------------
file_path = r"D:\ED\FIFS\data\bowling.csv"  # Adjust path as needed
df = pd.read_csv(file_path)
df["Match Date"] = pd.to_datetime(df["Match Date"])
df["venue"] = df["venue"].str.strip()  # Clean extra spaces if any

# ----------------------------------------
# Define required lists (provided)
# ----------------------------------------
bowlers = [80247.0, 1174726.0, 80259.0, 67750.0, 90231.0, 57022.0, 61861.0, 84865.0, 87051.0, 46888.0,
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

# ----------------------------------------
# Precompute latest-match lookups for various groupings.
# ----------------------------------------
bowler_latest = get_latest_rows(df, ["bowler"])
bowl_team_latest = get_latest_rows(df, ["bowl_team"])
bowler_vs_opp = get_latest_rows(df, ["bowler", "opposition"])
bowl_team_vs_opp = get_latest_rows(df, ["bowl_team", "opposition"])
all_teams_vs_opp = get_latest_rows(df, ["opposition"])
bowler_inn = get_latest_rows(df, ["bowler", "innings"])
bowl_team_inn = get_latest_rows(df, ["bowl_team", "innings"])
all_teams_inn = get_latest_rows(df, ["innings"])
bowler_venue = get_latest_rows(df, ["bowler", "venue"])
bowl_team_venue = get_latest_rows(df, ["bowl_team", "venue"])
all_teams_venue = get_latest_rows(df, ["venue"])

# ----------------------------------------
# Generate all valid combinations (each bowler, for every opponent, venue, and innings)
# ----------------------------------------
data_combinations = []
for bowler in bowlers:
    # Determine the bowler's team (using mode from the full dataset)
    bowler_rows = df[df["bowler"] == bowler]
    if bowler_rows.empty:
        continue  # Skip if no record exists for this bowler
    bowl_team = bowler_rows["bowl_team"].mode().iloc[0]

    # Opponents: all teams except the bowler's own team
    opponents = [team for team in teams if team != bowl_team]

    # Generate combinations: (opposition, venue, innings)
    for opposition, venue, inn in product(opponents, venues, innings):
        data_combinations.append((bowler, bowl_team, opposition, venue, inn))

generated_df = pd.DataFrame(data_combinations,
                            columns=["bowler", "bowl_team", "opposition", "venue", "innings"])


# ----------------------------------------
# Helper: Safe lookup from a precomputed dictionary
# ----------------------------------------
def lookup_value(lookup_dict, key, stat_col):
    row = lookup_dict.get(key, None)
    return row[stat_col] if row is not None and stat_col in row else None


# ----------------------------------------
# Define the statistic columns to populate.
# The generated dataset should have these 34 columns:
# bowler, bowl_team, opposition, venue, innings,
# bowler_avg, bowler_eco, bowler_sr, bowler_wpm,
# bowl_team_avg,
# bowler_avg_opp, bowler_eco_opp, bowler_sr_opp, bowler_wpm_opp,
# bowl_team_avg_opp, all_team_avg_opp,
# bowler_avg_inn, bowler_sr_inn, bowler_wpm_inn, bowler_eco_inn,
# bowl_team_avg_inn, all_team_avg_inn,
# bowler_avg_ven, bowler_sr_ven, bowler_wpm_ven, bowler_eco_ven,
# bowl_team_avg_ven, all_team_avg_ven,
# bowler_avg_last5, bowler_eco_last5, bowler_sr_last5, bowler_wpm_last5,
# bowling_fp, matchup_score
# ----------------------------------------
stats_columns = [
    "bowler_avg", "bowler_eco", "bowler_sr", "bowler_wpm",
    "bowl_team_avg",
    "bowler_avg_opp", "bowler_eco_opp", "bowler_sr_opp", "bowler_wpm_opp",
    "bowl_team_avg_opp", "all_team_avg_opp",
    "bowler_avg_inn", "bowler_sr_inn", "bowler_wpm_inn", "bowler_eco_inn",
    "bowl_team_avg_inn", "all_team_avg_inn",
    "bowler_avg_ven", "bowler_sr_ven", "bowler_wpm_ven", "bowler_eco_ven",
    "bowl_team_avg_ven", "all_team_avg_ven",
    "bowler_avg_last5", "bowler_eco_last5", "bowler_sr_last5", "bowler_wpm_last5",
    "bowling_fp", "matchup_score"
]


# ----------------------------------------
# Populate each generated row with the latest match statistics
# ----------------------------------------
def populate_row(row):
    bowler = row["bowler"]
    bowl_team = row["bowl_team"]
    opposition = row["opposition"]
    venue = row["venue"]
    inn = row["innings"]

    vals = {}

    # Bowler-specific stats (from the bowler's latest match)
    bowler_data = bowler_latest.get(bowler, None)
    for stat in ["bowler_avg", "bowler_eco", "bowler_sr", "bowler_wpm",
                 "bowler_avg_last5", "bowler_eco_last5", "bowler_sr_last5", "bowler_wpm_last5",
                 "bowling_fp", "matchup_score"]:
        vals[stat] = bowler_data[stat] if bowler_data is not None else None

    # Bowl team overall stats (latest match for bowl_team)
    team_data = bowl_team_latest.get(bowl_team, None)
    vals["bowl_team_avg"] = team_data["bowl_team_avg"] if team_data is not None else None

    # Bowler vs. Opposition stats
    for stat in ["bowler_avg_opp", "bowler_eco_opp", "bowler_sr_opp", "bowler_wpm_opp"]:
        vals[stat] = lookup_value(bowler_vs_opp, (bowler, opposition), stat)

    # Bowl team vs. Opposition stats
    vals["bowl_team_avg_opp"] = lookup_value(bowl_team_vs_opp, (bowl_team, opposition), "bowl_team_avg_opp")

    # All teams vs. Opposition stats
    vals["all_team_avg_opp"] = lookup_value(all_teams_vs_opp, opposition, "all_team_avg_opp")

    # Bowler in specific Innings stats
    for stat in ["bowler_avg_inn", "bowler_sr_inn", "bowler_wpm_inn", "bowler_eco_inn"]:
        vals[stat] = lookup_value(bowler_inn, (bowler, inn), stat)

    # Bowl team in Innings stats
    vals["bowl_team_avg_inn"] = lookup_value(bowl_team_inn, (bowl_team, inn), "bowl_team_avg_inn")

    # All teams in Innings stats
    vals["all_team_avg_inn"] = lookup_value(all_teams_inn, inn, "all_team_avg_inn")

    # Bowler at Venue stats
    for stat in ["bowler_avg_ven", "bowler_sr_ven", "bowler_wpm_ven", "bowler_eco_ven"]:
        vals[stat] = lookup_value(bowler_venue, (bowler, venue), stat)

    # Bowl team at Venue stats
    vals["bowl_team_avg_ven"] = lookup_value(bowl_team_venue, (bowl_team, venue), "bowl_team_avg_ven")

    # All teams at Venue stats
    vals["all_team_avg_ven"] = lookup_value(all_teams_venue, venue, "all_team_avg_ven")

    return pd.Series(vals)


# Apply the population function to each generated row
stats_df = generated_df.apply(populate_row, axis=1)

# Combine the base combination columns with the populated statistics
final_df = pd.concat([generated_df, stats_df], axis=1)

# ----------------------------------------
# Save the final dataset to CSV
# ----------------------------------------
output_path = "generated_bowling_data.csv"
final_df.to_csv(output_path, index=False)
print(f"Dataset saved as {output_path}")
