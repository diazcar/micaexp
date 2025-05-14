# %%
import sys

sys.path.append("/home/lucasheinry/code/micaexp")
from src.routines.microspot_api import request_microspot


# %%
import os

request_microspot(
    aggregation="horaire",
    timezone="Africa/Maputo",
    studies=[],
    campaigns=[],
    observationTypeCodes=["24", "39"],
    devices=[],
    dateRange=["2024-01-01T01:00:00+00:00", "2024-12-31T23:00:00+00:00"],
    url="https://spot.atmo-france.org/export-api/observations",
    headers={
        "Authorization": f"Bearer {os.getenv('MICROSPOT_REQUEST_KEY')}",
        "Content-Type": "application/json",
    },
)
# %%
