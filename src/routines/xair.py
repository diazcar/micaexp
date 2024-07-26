import os
import warnings
import requests
import datetime as dt
import pandas as pd
import numpy as np

from src.fonctions import mask_duplicates

ISO = {
    'PM10': '24',
    'PM2.5': '39',
    'PM1': '68',
}

JSON_PATH_LISTS = {
    'sites': {
        'record_path': None,
        'meta': [
            'id',
            'labelSite',
            'startDate',
            'stopDate',
            ['address', ['department', 'id']],
            ['address', ['department', 'labelDepartment']],
            ['address', ['commune', 'labelCommune']],
            ['adress', 'latitude'],
            ['adress', 'longitude'],
            ['environment', 'locationTypeLabel'],
            ['environment', 'classTypeLabel'],
            ['sectors', 'zoneOfActivityLabel'],

        ]
    },
    'measures': {
        'record_path': None,
        'meta': [
            'id',
            ['site', 'id'],
            ['physical', 'tagPhy'],
            ['physical', 'id'],
            ['unit', 'id'],
        ],
    },
    'data': {
        'record_path': ['sta', 'data',],
        'meta': [
            'id',
            ['sta', 'unit', 'id'],
        ],
    },
    'physicals': {
        'record_path': None,
        'meta': None,
    },
}

HEADER_RENAME_LISTS = {
    'sites': {
        'id': 'id',
        'labelSite': 'labelSite',
        'address.department.id': 'dept_code',
        'address.department.labelDepartment': 'labelDepartment',
        'address.commune.labelCommune': 'labelCommune',
        'address.latitude': 'latitude',
        'address.longitude': 'longitude',
        'environment.locationTypeLabel': 'locationTypeLabel',
        'environment.classTypeLabel': 'classTypeLabel',
        'sectors.zoneOfActivityLabel': 'zoneOfActivityLabel',
    },
    'measures': {
        'id': 'id',
        'site.id': 'id_site',
        'physical.tagPhy': 'phy_name',
        'physical.id': 'id_phy',
        'unit.id': 'unit',
    },
    'data': {
        'id': 'id',
        'sta.unit.id': 'unit',
        'value': 'value',
        'date': 'date',
        'state': 'state',
    },
    'physicals': {
        'id': 'id',
        'chemicalSymbol': 'chemicalSymbol',
        'label': 'long_name',
    },
}

URL_DICT = {
    "data": "https://172.16.13.224:8443/dms-api/public/v2/data?",
    "sites": "https://172.16.13.224:8443/dms-api/public/v2/sites?",
    "physicals": "https://172.16.13.224:8443/dms-api/public/v1/physicals?",
    "measures": "https://172.16.13.224:8443/dms-api/public/v2/measures?",
}

DATA_KEYS = {
    "data": "data",
    "sites": "sites",
    "physicals": "physicals",
    "measures": "measures",
}

DATA_KEYS = {
    "data": "data",
    "sites": "sites",
    "physicals": "physicals",
    "measures": "measures",
}

DATATYPES = {
    'quart-horaire': 'base',
    'horaire': 'hourly'
}


def wrap_xair_request(
        fromtime: str,
        totime: str,
        keys: str,
        sites: list[str,],
        physicals: list[str,],
        datatype: str = "hourly",
) -> pd.DataFrame:

    xair_site_measures = request_xr(
        folder=DATA_KEYS['measures'],
        sites=sites,
        physicals=physicals,
    )

    fromtime, totime = format_time_for_xair(
        fromtime,
        totime)

    xair_data_raw = request_xr(
        fromtime=fromtime,
        totime=totime,
        folder=DATA_KEYS['data'],
        measures=",".join(xair_site_measures['id'].to_list()),
        datatype=datatype,
    )

    xair_data_raw['date'] = pd.to_datetime(
        xair_data_raw['date'],
        format="%Y-%m-%dT%H:%M:%SZ"
        )
    xair_data_raw.set_index('date', inplace=True)

    xair_data = mask_aorp(xair_data_raw)

    xair_data = mask_duplicates(
        data=xair_data,
        site_name=sites,
        poll_iso=physicals,
        )
    print()
    return (xair_data)


def format_time_for_xair(
        fromtime: np.datetime64,
        totime: np.datetime64,
):
    fromtime = dt.datetime.strptime(
        fromtime.split(".")[0],
        "%Y-%m-%dT%H:%M:%S"
        )
    totime = dt.datetime.strptime(
        totime.split(".")[0],
        "%Y-%m-%dT%H:%M:%S"
        )

    return (
        fromtime.strftime(format="%Y-%m-%dT%H:%M:%SZ"),
        totime.strftime(format="%Y-%m-%dT%H:%M:%SZ")
        )


def time_window(
        format_str: str = None,
        date: str = None,

        ):

    days = 5
    time_delta = dt.timedelta(days)

    if date:
        time_now = dt.datetime.strptime(date, format)
    else:
        time_now = dt.datetime.now()

    end_time = dt.datetime.combine(
        time_now,
        dt.datetime.max.time()
        )

    start_time = dt.datetime.combine(
        time_now-time_delta,
        dt.datetime.min.time()
        )

    if format_str:
        return (
            start_time.strftime(format=format_str),
            end_time.strftime(format=format_str)
            )
    else:
        return (
            start_time,
            end_time
        )


def request_xr(
    fromtime: str = "",
    totime: str = "",
    folder: str = "",
    datatype: str = "base",
    groups: str = "",
    sites: str = "",
    measures: str = "",
    physicals: str = "",
    header_for_df: list = None
) -> pd.DataFrame:
    """
    Get json objects from XR rest api

    input :
    -------
        fromtime : str
            Start time  in YYYY-MM-DDThh:mm:ssZ format
        totime : str
            End time  in YYYY-MM-DDThh:mm:ssZ format
        folder : str
            Url string to request XR rest api
            Default = "data"
        dataTypes : str,
            Time mean in base(15min), hour, day, month
            Default = "base"
        groups : str
            Site groupes
            Default = "DIDON"
        sites : str
            site or list of sites to retrive
            Default = "" (all sistes)
        measures : str
            list of measure ids
            Default : str
    return :
    --------
        csv : csv file
            File in ../data directory
    """
    url = (
        f"{URL_DICT[folder]}&"
        f"from={fromtime}&"
        f"to={totime}&"
        f"sites={sites}&"
        f"dataTypes={datatype}&"
        f"groups={groups}&"
        f"measures={measures}&"
        f"physicals={physicals}&"
    )

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")

        request_data = requests.get(
            url, verify=False
            ).json()[DATA_KEYS[folder]]
        data = pd.json_normalize(
            data=request_data,
            record_path=JSON_PATH_LISTS[folder]['record_path'],
            meta=JSON_PATH_LISTS[folder]['meta'])
        for col in data.columns:
            if col not in list(HEADER_RENAME_LISTS[folder].keys()):
                data[col] = np.nan

    return (data.rename(columns=HEADER_RENAME_LISTS[folder]))


def build_dataframe(
        data: dict,
        header: list,
        datatype: str
        ) -> pd.DataFrame:

    out_df = pd.DataFrame(columns=header)
    for i in range(len(data[:])):
        df = pd.DataFrame(data[i][datatype]['data'])

        df["id"] = data[i]["id"]

        for col in header:
            if col not in df.columns:
                df.insert(2, col, None)

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            out_df = pd.concat([out_df, df],
                               join="inner",
                               ignore_index=True,
                               sort=False)

        out_df['date'] = pd.to_datetime(
            out_df['date'],
            format="%Y-%m-%dT%H:%M:%SZ"
            )

    return (out_df)


def test_path(path: str, mode: str):

    if mode == "mkdir":
        if os.path.exists(path) is False:
            os.mkdir(path)
    if mode == "makedirs":
        if os.path.exists(path) is False:
            os.makedirs(path)
    if mode == "remove_file":
        if os.path.exists(path):
            os.remove(path)


def get_moymax_data(
        data,
        measure_id,
        poll_site_info,
        threshold=0.75
        ):

    pd.options.mode.chained_assignment = None

    data.drop(['id'], axis=1, inplace=True)
    data['data_coverage'] = (~np.isnan(data['value'])).astype(int)

    moymax_jour = (
        data.resample('d')
        .mean()
        .rename(columns={'value': 'mean'})
        )
    moymax_jour['max'] = data['value'].resample('d').max()
    moymax_jour.loc[
        moymax_jour['data_coverage'] < threshold, ['mean', 'max']
        ] = np.nan

    site_info = poll_site_info[
        poll_site_info['id'] == measure_id
        ]

    add_poll_info(
        moymax_jour,
        site_info,
        site_info.columns.to_list()
        )

    return (moymax_jour)


def add_poll_info(
        data: pd.DataFrame,
        site_info: pd.DataFrame,
        columns: list,
        new_col: dict = None,
        ) -> pd.DataFrame:

    for head in columns:
        data.insert(
            0,
            head, site_info[head].iloc[0]
            )
    if new_col:
        for head in new_col:
            data.insert(
                0,
                head, new_col[head]
                )
    return (data)


def mask_aorp(data):

    data['value'] = data.apply(
        lambda row:
            np.nan
            if row['state'] not in ['A', 'O', 'R', 'P']
            else row['value'],
            axis=1
    )
    return (data[['id', 'value', 'unit']])


def get_figure_title(
    group_data: pd.DataFrame,
    group_sites: pd.DataFrame,
    id: str,
):
    """_summary_

    Parameters
    ----------
    group_data : pd.DataFrame
        _description_
    group_sites : pd.DataFrame
        _description_
    id : str
        _description_

    Returns
    -------
    _type_
        _description_
    """
    if "MOBILE" in id.upper():
        name = group_data[
            group_data['id'] == id
            ]['id_site'].values[0]
        site_name = group_sites[
            group_sites['id'] == name
            ]['labelSite'].values[0]
        dept_code = group_sites[
            group_sites['labelSite'] == site_name
            ]['dept_code'].values[0]

    else:
        site_name = group_data[
            group_data['id'] == id
            ]['id_site'].values[0]
        dept_code = group_sites[
            group_sites['id'] == site_name
            ]['dept_code'].values[0]

    return (site_name, dept_code)
