# %%
import sys
import pandas as pd
from src.api_calls.microspot_api import request_microspot

sys.path.append("/home/lucasheinry/code/micaexp")


# %%
import os

data = request_microspot(
    aggregation="horaire",
    timezone="Africa/Maputo",
    studies=[],
    campaigns=[],
    observationTypeCodes=["24", "39"],
    devices=[2521,2531,2544],
    dateRange=["2025-01-01T01:00:00+00:00", "2026-12-31T23:00:00+00:00"],
    url="https://spot.atmo-france.org/export-api/observations",
    headers={
        "Authorization": f"Bearer {os.getenv('MICROSPOT_REQUEST_KEY')}",
        "Content-Type": "application/json",
    },
)
# %%


# take data with date between 10 april 2025 and 7 may 2025
# ensure data index is in datetime64 format
data.index = pd.to_datetime(data.index).tz_localize("UTC")

data_filtered = data.loc[
    (data.index >= pd.to_datetime("2025-04-10T00:00:00+00:00"))
    & (data.index <= pd.to_datetime("2025-05-07T23:00:00+00:00"))
]

#%%

# Ensure required columns exist
for col in ['capteur_id', 'isoCode']:
    if col not in data_filtered.columns:
        raise ValueError(f"Column '{col}' not found in data_filtered")

# Add a 'week' column (ISO week)
data_filtered['week'] = data_filtered.index.isocalendar().week

# Group by week, capteur_id, and isoCode, then calculate mean of valueModified
weekly_means = (
    data_filtered
    .groupby(['week', 'capteur_id', 'isoCode'])['valueModified']
    .mean()
    .unstack(['capteur_id', 'isoCode'])
)

# Rename isoCode columns: 24 -> PM10, 39 -> PM2.5
weekly_means.columns = [
    (capteur_id, 'PM10' if isoCode == "24" else 'PM2.5' if isoCode == "39" else isoCode)
    for capteur_id, isoCode in weekly_means.columns
]
weekly_means.columns = pd.MultiIndex.from_tuples(weekly_means.columns, names=['capteur_id', 'Pollutant'])

print(weekly_means)


# %%
# round the values to 2 decimal places
weekly_means = weekly_means.round(2)


# Save the DataFrame to a CSV file in /mnt/c/Users/lucas.heinry/OneDrive - ATMOSUD/Documents/Surveillance calanques

output_path = "/mnt/c/Users/lucas.heinry/OneDrive - ATMOSUD/Documents/Surveillance calanques/weekly_means.csv"
weekly_means.to_csv(output_path)
print(f"Data saved to {output_path}")

# %%
