import numpy as np
import pandas as pd
import geopandas as gp
from src.glob_vars import SEUILS
from src.routines.microspot_api import request_microspot
from src.routines.xair import ISO, request_xr


def list_of_strings(arg):
    return arg.split(',')


def weekday_profile(
        aggregation: str,
        capteur_value_var: str,
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
        for col in ['valueRaw', 'value']:
            grouped_data = days_data[[index, col]].groupby(
                days_data[index].dt.time
                ).mean().drop([index], axis=1)
            out_data = pd.concat(
                [out_data, grouped_data],
                axis=1
            )
        datime_format = '%H:%M:%S'

    if aggregation == 'horaire':
        for col in ['valueModified', 'value']:
            grouped_data = days_data[[index, col]].groupby(
                days_data[index].dt.hour
                ).mean().drop([index], axis=1)
            out_data = pd.concat(
                [out_data, grouped_data],
                axis=1
            )
        datime_format = '%H'

    # if aggregation == 'journalière':
    #     for col in ['valueModified', 'value']:
    #         grouped_data = days_data[[index, col]].groupby(
    #             days_data[index].dt.day
    #             ).mean().drop([index], axis=1)
    #         out_data = pd.concat(
    #             [out_data, grouped_data],
    #             axis=1
    #         )
    #     datime_format = '%d'

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
        hour_data: pd.DataFrame,
        minmax_data: pd.DataFrame,
        poll: str,
):
    seuil_information = SEUILS[poll]['FR']['seuil_information']
    seuil_alert = SEUILS[poll]['FR']['seuil_alerte']

    if poll in ['PM10', 'PM2.5']:
        moyenne_periode = round(hour_data.mean())
        min_periode = round(minmax_data.min())
        max_periode = round(minmax_data.max())

        if moyenne_periode.isna().all():
            for i in range(1):
                moyenne_periode[i] = 0
                min_periode[i] = 0
                max_periode[i] = 0

        count_seuil_information = (
            hour_data[hour_data > seuil_information]
            .count()
            )

        count_seuil_alert = (
            hour_data[hour_data > seuil_alert]
            .count()
            )

    else:
        moyenne_periode = round(minmax_data.mean())
        min_periode = round(minmax_data.min())
        max_periode = round(minmax_data.max())
        count_seuil_information = 'N/A'
        count_seuil_alert = 'N/A'

    return (
        count_seuil_information,
        count_seuil_alert,
        moyenne_periode,
        min_periode,
        max_periode,
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


def validate_and_aggregate(
        data: pd.DataFrame,
        threshold: int = 0.75,
):
    data['data_coverage'] = (~np.isnan(data['valueModified'])).astype(int)

    hour_data = data.resample('H').mean()
    hour_data.loc[
        hour_data['data_coverage'] < threshold, ['valueModified', 'value']
        ] = np.nan
    hour_data.drop(['data_coverage'], axis=1, inplace=True)

    day_data = data.resample('D').mean()
    day_data.loc[
        day_data['data_coverage'] < threshold, ['valueModified', 'value']
        ] = np.nan
    day_data.drop(['data_coverage'], axis=1, inplace=True)

    data.drop(['data_coverage'], axis=1, inplace=True)

    return (hour_data, day_data)


def get_geoDF(
        id_capteur: str,
        polluant: str,
        start_date: str,
        end_date: str,
        nom_station: str,
):

    capteur_data = request_microspot(
        observationTypeCodes=[ISO[polluant]],
        devices=[id_capteur],
        aggregation='horaire',
        dateRange=[f"{start_date}T00:00:00+00:00", f"{end_date}T00:00:00+00:00"],
    )

    station_json = request_xr(
        folder='sites',
        sites=nom_station,
    )
    df = pd.DataFrame(
        data={
            'site_name': [
                capteur_data['site_name'].values[0],
                station_json['labelSite'].values[0],
                ],
            'lon': [
                capteur_data['site_lon'].values[0],
                station_json['longitude'].values[0],
                ],
            'lat': [
                capteur_data['site_lat'].values[0],
                station_json['latitude'].values[0],
                ]
        }
    )

    gdf = gp.GeoDataFrame(
        df,
        geometry=gp.points_from_xy(
            df.lon,
            df.lat
        ),
        crs="EPSG:3857",
    )

    return gdf


def get_zoom_level_and_center(longitudes=None, latitudes=None):
        """Function documentation:\n
        Basic framework adopted from Krichardson under the following thread:
        https://community.plotly.com/t/dynamic-zoom-for-mapbox/32658/7

        # NOTE:
        # THIS IS A TEMPORARY SOLUTION UNTIL THE DASH TEAM IMPLEMENTS DYNAMIC ZOOM
        # in their plotly-functions associated with mapbox, such as go.Densitymapbox() etc.

        Returns the appropriate zoom-level for these plotly-mapbox-graphics along with
        the center coordinate tuple of all provided coordinate tuples.
        """

        if ((latitudes is None or longitudes is None)
                or (len(latitudes) != len(longitudes))):
            return 0, (0, 0)

        # Get the boundary-box 
        b_box = {} 
        b_box['height'] = latitudes.max()-latitudes.min()
        b_box['width'] = longitudes.max()-longitudes.min()
        b_box['center'] = (np.mean(longitudes), np.mean(latitudes))

        # get the area of the bounding box in order to calculate a zoom-level
        area = (b_box['height']*1.5) * (b_box['width']*1.5)

        # * 1D-linear interpolation with numpy:
        # - Pass the area as the only x-value and not as a list, in order to return a scalar as well
        # - The x-points "xp" should be in parts in comparable order of magnitude of the given area
        # - The zpom-levels are adapted to the areas, i.e. start with the smallest area possible of 0
        # which leads to the highest possible zoom value 20, and so forth decreasing with increasing areas
        # as these variables are antiproportional
        zoom = np.interp(
            x=area,
            xp=[0, 6**-10, 5**-10, 4**-10, 3**-10, 2**-10, 1**-10, 1**-5],
            fp=[24, 20, 15,    14,     13,     12,     7,      5]
            )

        # Finally, return the zoom level and the associated boundary-box center coordinates
        return zoom, b_box['center']


def save_dataframes(
        dataframe_list: list[pd.DataFrame],
        path: str
):
    for i, df in enumerate(dataframe_list):
        df.to_csv(f"{path}/data{i}.csv")
