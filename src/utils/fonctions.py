import numpy as np
import pandas as pd
import geopandas as gp
import plotly.colors
from src.utils.glob_vars import SEUILS
from src.api_calls.microspot_api import request_microspot
from src.api_calls.xair import ISO, request_xr


def weekday_profile(
    data: pd.DataFrame,
    week_section: str,
):
    # Ensure index has a name, fallback to 'date'
    index = data.index.name or "date"
    if data.index.name is None:
        data.index.name = "date"
    data.reset_index(inplace=True)
    if week_section == "workweek":
        days_data = data[data[index].dt.weekday < 5]
    if week_section == "weekend":
        days_data = data[data[index].dt.weekday > 4]

    out_data = pd.DataFrame()

    for col in days_data.columns:
        grouped_data = (
            days_data[[index, col]]
            .groupby(days_data[index].dt.time)
            .mean()
            .drop([index], axis=1)
        )
        out_data = pd.concat([out_data, grouped_data], axis=1)
    datime_format = "%H:%M:%S"

    out_data.index.name = "heure"
    out_data.reset_index(inplace=True)
    out_data["heure"] = pd.to_datetime(out_data["heure"], format=datime_format)
    out_data.set_index("heure", inplace=True)

    data.set_index(index, inplace=True)
    return out_data


def get_stats(
    hour_data: pd.DataFrame,
    minmax_data: pd.DataFrame,
    poll: str,
):
    seuil_information = SEUILS[poll]["FR"]["seuil_information"]
    seuil_alert = SEUILS[poll]["FR"]["seuil_alerte"]

    if poll in ["PM10", "PM2.5"]:
        moyenne_periode = round(hour_data.mean())
        min_periode = round(minmax_data.min())
        max_periode = round(minmax_data.max())

        if moyenne_periode.isna().all():
            for i in range(1):
                moyenne_periode[i] = 0
                min_periode[i] = 0
                max_periode[i] = 0

        count_seuil_information = hour_data[hour_data > seuil_information].count()

        count_seuil_alert = hour_data[hour_data > seuil_alert].count()

    else:
        moyenne_periode = round(minmax_data.mean())
        min_periode = round(minmax_data.min())
        max_periode = round(minmax_data.max())
        count_seuil_information = "N/A"
        count_seuil_alert = "N/A"

    return (
        count_seuil_information,
        count_seuil_alert,
        moyenne_periode,
        min_periode,
        max_periode,
        seuil_information,
        seuil_alert,
    )


def get_color_map(columns):
    """
    Assigns 'firebrick' to 'station' and Plotly default colors to other columns.
    """
    default_colors = plotly.colors.qualitative.Plotly
    color_map = {}
    color_iter = iter(default_colors)
    for col in columns:
        if col == "station":
            color_map[col] = "firebrick"
        else:
            color_map[col] = next(color_iter)
    return color_map


def graph_title(
    graph_type: str,
    aggregation: str,
    polluant: str,
):
    if graph_type == "timeseries":
        if aggregation == "quart-horaire":
            title = f"Concentration {aggregation} en {polluant}"
        if aggregation == "horaire":
            title = f"Concentrations moyennes horaires en {polluant}"
        if aggregation == "journalière":
            title = f"Concentrations moyennes journalièrs en {polluant}"
    if graph_type == "boxplot":
        if aggregation == "quart-horaire":
            title = f"Distribution des concentrations quart-horaire en {polluant}"
        if aggregation == "horaire":
            title = f"Distribution des concentrations horaires en {polluant}"
        if aggregation == "journalière":
            title = f"Distribution des concentrations journalièrs en {polluant}"
    return title


def get_geoDF(
    id_capteur: list,  # can be int, str, or list
    polluant: str,
    start_date: str,
    end_date: str,
    nom_station: str,
):
    # Collect info for all sensors
    site_names = []
    lons = []
    lats = []

    for capteur_id in id_capteur:
        capteur_data = request_microspot(
            observationTypeCodes=[ISO[polluant]],
            devices=[capteur_id],
            aggregation="horaire",
            dateRange=[f"{start_date}T00:00:00+00:00", f"{end_date}T00:00:00+00:00"],
        )
        site_names.append(capteur_data["site_name"].values[0])
        lons.append(capteur_data["site_lon"].values[0])
        lats.append(capteur_data["site_lat"].values[0])

    # Add station info only if provided
    if nom_station:
        station_json = request_xr(
            folder="sites",
            sites=nom_station,
        )
        site_names.append(station_json["labelSite"].values[0])
        lons.append(station_json["longitude"].values[0])
        lats.append(station_json["latitude"].values[0])

    df = pd.DataFrame(
        data={
            "site_name": site_names,
            "lon": lons,
            "lat": lats,
        }
    )

    gdf = gp.GeoDataFrame(
        df,
        geometry=gp.points_from_xy(df.lon, df.lat),
        crs="EPSG:3857",
    )

    return gdf
