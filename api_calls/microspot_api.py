import requests
import json
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

DATA_AGG_DIC = {"quart-horaire": "15 m", "horaire": "1 h"}


def add_columns_info(
    observations: pd.DataFrame,
    capteur_info: dict,
    campaign_info: dict,
):
    """_summary_

    Parameters
    ----------
    capteur_info : dict
        _description_
    campagne_info : dict
        _description_
    site_info : dict
        _description_
    """

    capteur_id = capteur_info["id"]
    capteur_scaninterval = capteur_info["scanInterval"]

    campaign_id = campaign_info["id"]
    campaign_name = campaign_info["campaign.name"]
    if "location" in campaign_info.index and campaign_info["location"] == None:
        site_id = None
        site_name = None
        site_lon = None
        site_lat = None
    else:
        site_id = campaign_info["location.id"]
        site_name = campaign_info["location.name"]
        site_lon = campaign_info["location.position"][1]
        site_lat = campaign_info["location.position"][0]

    observations["capteur_id"] = capteur_id
    observations["ScanInterval"] = capteur_scaninterval
    observations["campaign_id"] = campaign_id
    observations["campaign_name"] = campaign_name
    observations["site_id"] = site_id
    observations["site_name"] = site_name
    observations["site_lon"] = site_lon
    observations["site_lat"] = site_lat


def response_to_dataframe(
    json_data: json,
):
    capteurs = pd.json_normalize(json_data)
    data = pd.DataFrame()

    for i_capteur in range(len(capteurs.index)):
        campaigns = pd.json_normalize(capteurs.iloc[i_capteur]["datastreams"])
        for i_campaign in range(len(campaigns.index)):
            observations = pd.json_normalize(campaigns.iloc[i_campaign]["observations"])
            add_columns_info(
                observations=observations,
                capteur_info=capteurs.iloc[i_capteur],
                campaign_info=campaigns.iloc[i_campaign],
            )
            data = pd.concat([data, observations])

    # Only process if data is not empty and has 'happenedAt'
    if data.empty or "happenedAt" not in data.columns:
        return pd.DataFrame()

    data.rename(columns={"happenedAt": "date"}, inplace=True)
    data["date"] = (
        pd.to_datetime(data["date"]).dt.tz_convert("UTC").dt.tz_localize(None)
    )
    data.reset_index(inplace=True)
    data.set_index("date", inplace=True)

    return data


def request_microspot(
    aggregation: str,
    timezone: str = "Europe/Paris",
    studies: list = [],
    campaigns: list = [],
    observationTypeCodes: list = ["24"],
    devices: list[int] = [],
    dateRange: list = ["2024-01-01T01:00:00+00:00", "2024-01-30T01:00:00+00:00"],
    url: str = "https://spot.atmo-france.org/export-api/observations",
    headers: dict = {
        "Authorization": f"Bearer {os.getenv('MICROSPOT_REQUEST_KEY')}",
        "Content-Type": "application/json",
    },
):
    """_summary_

    Parameters
    ----------
    timezone : str, optional
        by default "Europe/Paris"

    studies : list, optional
        Study name,
        by default []

    campaigns : list, optional
        Campaign ID,
        by default []

    observationTypeCodes : list, optional
        Pollutant ISO,
        by default ["24"]

    devices : list, optional
        Capteur ID,
        by default []

    aggregation : str, optional
        Time aggregation in ['1 h', '15 m'],
        by default "1 h"

    dateRange : list, optional
        Date range with time zone information,
        by default [ "2024-01-01T01:00:00+00:00", "2024-01-30T01:00:00+00:00" ]

    url : str, optional
        by default "https://spot.atmo-france.org/export-api/observations"

    headers : dict, optional
        by default {
            "Authorization": f"Bearer {os.getenv('MICROSPOT_REQUEST_KEY')}",
            "Content-Type": "application/json",
            }


    Returns
    -------
    pd.DataFrame
        _description_
    """

    json_data = {
        "timezone": timezone,
        "studies": studies,
        "campaigns": campaigns,
        "observationTypeCodes": observationTypeCodes,
        "devices": devices,
        "aggregation": DATA_AGG_DIC[aggregation],
        "dateRange": dateRange,
    }

    response = requests.post(url, json=json_data, headers=headers).json()
    return response_to_dataframe(response)
