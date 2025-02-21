import pandas as pd
from itertools import product

# Load the full dataset
file_path = r"D:\ED\FIFS\data\batting.csv"
df = pd.read_csv(file_path)

# Convert match dates to datetime
df["Match Date"] = pd.to_datetime(df["Match Date"])

# Define required batters, venues, teams, and innings
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

# Generate all valid combinations
data_combinations = []
for batter in batters:
    bat_team = df[df["batter"] == batter]["bat_team"].mode().values
    if len(bat_team) == 0:
        continue  # Skip if no team found
    bat_team = bat_team[0]

    opponents = [team for team in teams if team != bat_team]  # Exclude player's own team

    for opposition, venue, inning in product(opponents, venues, innings):
        data_combinations.append((batter, bat_team, opposition, venue, inning))

# Convert combinations into DataFrame
generated_df = pd.DataFrame(data_combinations, columns=["batter", "bat_team", "opposition", "venue", "innings"])

# Function to get latest stats for a given batter and condition
def get_latest_stat(batter, condition_col, condition_val, stat_col):
    subset = df[(df["batter"] == batter) & (df[condition_col] == condition_val)]
    latest_match = subset.sort_values("Match Date", ascending=False).head(1)
    return latest_match[stat_col].values[0] if not latest_match.empty else None

# Extract latest stats for each generated row
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

for col in stats_columns:
    generated_df[col] = generated_df.apply(lambda row: get_latest_stat(row["batter"], row["venue"], row["venue"], col), axis=1)

# Save the generated dataset
output_path = "generated_batting_data.csv"
generated_df.to_csv(output_path, index=False)
print(f"Dataset saved as {output_path}")
