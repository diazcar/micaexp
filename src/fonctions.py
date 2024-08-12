import numpy as np
import pandas as pd
from src.glob_vars import SEUILS


def list_of_strings(arg):
    return arg.split(',')


def weekday_profile(
        aggregation: str,
        data: pd.DataFrame,
        week_section: str,
):
    index = data.index.name
    data.reset_index(inplace=True)
    if week_section == 'workweek':
        days_data = data[data[index].dt.weekday < 5]
    if week_section == 'weekend':
        days_data = data[data[index].dt.weekday > 4]

    out_data = pd.DataFrame()
    if aggregation == 'quart-horaire':
        for col in ['valeur_ref', 'value']:
            grouped_data = days_data[[index, col]].groupby(
                days_data[index].dt.time
                ).mean().drop([index], axis=1)
            out_data = pd.concat(
                [out_data, grouped_data],
                axis=1
            )
        datime_format = '%H:%M:%S'

    if aggregation == 'horaire':
        for col in ['valeur_ref', 'value']:
            grouped_data = days_data[[index, col]].groupby(
                days_data[index].dt.hour
                ).mean().drop([index], axis=1)
            out_data = pd.concat(
                [out_data, grouped_data],
                axis=1
            )
        datime_format = '%H'
    
    if aggregation == 'journalière':
        for col in ['valeur_ref', 'value']:
            grouped_data = days_data[[index, col]].groupby(
                days_data[index].dt.day
                ).mean().drop([index], axis=1)
            out_data = pd.concat(
                [out_data, grouped_data],
                axis=1
            )
        datime_format = '%d'

    out_data.index.name = 'heure'
    out_data.reset_index(inplace=True)
    out_data['heure'] = pd.to_datetime(out_data['heure'], format=datime_format)
    out_data.set_index('heure', inplace=True)

    data.set_index('date', inplace=True)
    return out_data


def get_max(
        data1: pd.DataFrame,
        data2: pd.DataFrame,
        ):
    if data1.max().max() > data2.max().max():
        max = data1.max().max()
    else:
        max = data2.max().max()

    return max


def get_stats(
        data: pd.DataFrame,
        poll: str,
):
    seuil_information = SEUILS[poll]['FR']['seuil_information']
    seuil_alert = SEUILS[poll]['FR']['seuil_alerte']

    if poll == 'PM10':

        moyenne_periode = data.mean()

        count_seuil_information = (
            data[data > seuil_information]

            .count()
            )

        count_seuil_alert = (
            data[data > seuil_alert]
            .count()
            )

    else:
        moyenne_periode = data.mean()

        count_seuil_information = 'N/A'

        count_seuil_alert = 'N/A'

    return (
        count_seuil_information,
        count_seuil_alert,
        moyenne_periode,
        seuil_information,
        seuil_alert,
    )


def clean_outlayers(data: pd.DataFrame):

    for col in data.columns:
        Q1 = data[col].quantile(.50)
        Q2 = data[col].quantile(.99)
        iqr = Q2 - Q1
        upper = Q1 + 1.5*iqr

        data[col] = data[col].where(
            data[col].le(upper), np.nan
            )
    return data


def graph_title(
        graph_type: str,
        aggregation: str,
        polluant: str,
):
    if graph_type == 'timeseries':
        if aggregation == 'quart-horaire':
            title = f"Concentration {aggregation} en {polluant}"
        if aggregation == 'horaire':
            title = f"Concentrations moyennes horaires en {polluant}"
        if aggregation == 'journalière':
            title = f"Concentrations moyennes journalièrs en {polluant}"
    if graph_type == 'boxplot':
        if aggregation == 'quart-horaire':
            title = f"Distribution des concentrations quart-horaire en {polluant}"
        if aggregation == 'horaire':
            title = f"Distribution des concentrations horaires en {polluant}"
        if aggregation == 'journalière':
            title = f"Distribution des concentrations journalièrs en {polluant}"
    return title
