import numpy as np
import pandas as pd

from src.routines.xair import wrap_xair_request, ISO
from src.routines.microspot_api import request_microspot


def build_graph_data(
    start_date,
    end_date,
    site_plus_capteur,
    polluant,
    station_name=None,
):
    # Fetch station data only if station_name is provided
    if station_name:
        station_quart_data = wrap_xair_request(
            fromtime=start_date,
            totime=end_date,
            keys="data",
            sites=station_name,
            physicals=ISO[polluant],
            datatype="quart-horaire",
        )
        station_hour_data = wrap_xair_request(
            fromtime=start_date,
            totime=end_date,
            keys="data",
            sites=station_name,
            physicals=ISO[polluant],
            datatype="horaire",
        )
        station_col_name = "station"
        station_quart_data = station_quart_data.rename(
            columns={"value": station_col_name}
        )
        station_hour_data = station_hour_data.rename(
            columns={"value": station_col_name}
        )
    else:
        station_quart_data = None
        station_hour_data = None
        station_col_name = None

    capteur_quart_dfs = []
    capteur_hour_dfs = []

    for capteur in site_plus_capteur:
        cap_name, cap_id = capteur.rsplit(" - ", 1)
        cap_id = int(cap_id)
        micro_col_name = f"microcapteur_{cap_id}"

        capteur_quart_data = request_microspot(
            observationTypeCodes=[ISO[polluant]],
            devices=[cap_id],
            aggregation="quart-horaire",
            dateRange=[f"{start_date}T00:00:00+00:00", f"{end_date}T00:00:00+00:00"],
        )
        capteur_quart_data = capteur_quart_data[
            capteur_quart_data.isoCode == ISO[polluant]
        ]
        capteur_quart_data = capteur_quart_data.rename(
            columns={"valueRaw": micro_col_name}
        )
        capteur_quart_dfs.append(capteur_quart_data[[micro_col_name]])

        capteur_hour_data = request_microspot(
            observationTypeCodes=[ISO[polluant]],
            devices=[cap_id],
            aggregation="horaire",
            dateRange=[f"{start_date}T00:00:00+00:00", f"{end_date}T00:00:00+00:00"],
        )
        capteur_hour_data = capteur_hour_data[
            capteur_hour_data.isoCode == ISO[polluant]
        ]
        capteur_hour_data = capteur_hour_data.rename(
            columns={"valueModified": micro_col_name}
        )
        if micro_col_name not in capteur_hour_data.columns:
            capteur_hour_data[micro_col_name] = np.nan
        capteur_hour_dfs.append(capteur_hour_data[[micro_col_name]])

    if station_name and station_quart_data is not None:
        quart_data = pd.concat(
            [station_quart_data[station_col_name]] + capteur_quart_dfs, axis=1
        )
        hour_data = pd.concat(
            [station_hour_data[station_col_name]] + capteur_hour_dfs, axis=1
        )
    else:
        if not capteur_quart_dfs:
            date_index = pd.date_range(start=start_date, end=end_date, freq="15min")
            quart_data = pd.DataFrame(index=date_index)
        else:
            quart_data = pd.concat(capteur_quart_dfs, axis=1)

        if not capteur_hour_dfs:
            date_index = pd.date_range(start=start_date, end=end_date, freq="H")
            hour_data = pd.DataFrame(index=date_index)
        else:
            hour_data = pd.concat(capteur_hour_dfs, axis=1)

    return quart_data, hour_data
