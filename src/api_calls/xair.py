import os
import warnings
import requests
import datetime as dt
import pandas as pd
import numpy as np

ISO = {
    "PM10": "24",
    "PM2.5": "39",
    "PM1": "68",
}

JSON_PATH_LISTS = {
    "sites": {
        "record_path": None,
        "meta": [
            "id",
            "labelSite",
            "startDate",
            "stopDate",
            ["address", ["department", "id"]],
            ["address", ["department", "labelDepartment"]],
            ["address", ["commune", "labelCommune"]],
            ["adress", "latitude"],
            ["adress", "longitude"],
            ["environment", "locationTypeLabel"],
            ["environment", "classTypeLabel"],
            ["sectors", "zoneOfActivityLabel"],
        ],
    },
    "measures": {
        "record_path": None,
        "meta": [
            "id",
            ["site", "id"],
            ["physical", "tagPhy"],
            ["physical", "id"],
            ["unit", "id"],
        ],
    },
    "data_base": {
        "record_path": [
            "sta",
            "data",
        ],
        "meta": [
            "id",
            ["sta", "unit", "id"],
        ],
    },
    "data_hour": {
        "record_path": [
            "hourly",
            "data",
        ],
        "meta": [
            "id",
            ["hourly", "unit", "id"],
        ],
    },
    "physicals": {
        "record_path": None,
        "meta": None,
    },
}

HEADER_RENAME_LISTS = {
    "sites": {
        "id": "id",
        "labelSite": "labelSite",
        "address.department.id": "dept_code",
        "address.department.labelDepartment": "labelDepartment",
        "address.commune.labelCommune": "labelCommune",
        "address.latitude": "latitude",
        "address.longitude": "longitude",
        "environment.locationTypeLabel": "locationTypeLabel",
        "environment.classTypeLabel": "classTypeLabel",
        "sectors.zoneOfActivityLabel": "zoneOfActivityLabel",
    },
    "measures": {
        "id": "id",
        "site.id": "id_site",
        "physical.tagPhy": "phy_name",
        "physical.id": "id_phy",
        "unit.id": "unit",
    },
    "data": {
        "id": "id",
        "sta.unit.id": "unit",
        "hourly.unit.id": "unit",
        "value": "value",
        "date": "date",
        "state": "state",
    },
    "physicals": {
        "id": "id",
        "chemicalSymbol": "chemicalSymbol",
        "label": "long_name",
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

DATATYPES = {"quart-horaire": "base", "horaire": "hourly"}


def wrap_xair_request(
    fromtime: str,
    totime: str,
    keys: str,
    sites: list[str,],
    physicals: list[str,],
    datatype: str = "hourly",
) -> pd.DataFrame:

    xair_site_measures = request_xr(
        folder=DATA_KEYS["measures"],
        sites=sites,
        physicals=physicals,
    )

    fromtime, totime = format_time_for_xair(fromtime, totime)

    xair_data_raw = request_xr(
        fromtime=fromtime,
        totime=totime,
        folder=DATA_KEYS["data"],
        measures=",".join(xair_site_measures["id"].to_list()),
        datatype=DATATYPES[datatype],
    )

    xair_data_raw["date"] = pd.to_datetime(
        xair_data_raw["date"], format="%Y-%m-%dT%H:%M:%SZ"
    )
    xair_data_raw.set_index("date", inplace=True)
    xair_data = mask_aorp(xair_data_raw)

    xair_data = mask_duplicates(
        data=xair_data,
        site_name=sites,
        poll_iso=physicals,
    )

    return xair_data


def format_time_for_xair(
    fromtime: np.datetime64,
    totime: np.datetime64,
):

    fromtime = dt.datetime.strptime(
        f'{fromtime.split("T")[0]}T00:00:00', "%Y-%m-%dT%H:%M:%S"
    )
    totime = dt.datetime.strptime(
        f'{totime.split("T")[0]}T00:00:00', "%Y-%m-%dT%H:%M:%S"
    )

    return (
        fromtime.strftime(format="%Y-%m-%dT%H:%M:%SZ"),
        totime.strftime(format="%Y-%m-%dT%H:%M:%SZ"),
    )


def time_window(
    format: str = None,
    date: str = None,
):

    days = 5
    time_delta = dt.timedelta(days)

    if date:
        time_now = dt.datetime.strptime(date, format)
    else:
        time_now = dt.datetime.today()

    end_time = dt.datetime.combine(time_now, dt.datetime.max.time())

    start_time = dt.datetime.combine(time_now - time_delta, dt.datetime.min.time())

    if format:
        return (start_time.strftime(format=format), end_time.strftime(format=format))
    else:
        return (start_time, end_time)


def request_xr(
    fromtime: str = "",
    totime: str = "",
    folder: str = "",
    datatype: str = "base",
    groups: str = "",
    sites: str = "",
    measures: str = "",
    physicals: str = "",
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
    print(url)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")

        request_data = requests.get(url, verify=False).json()[DATA_KEYS[folder]]

        if folder == "data":
            if datatype == "base":
                data = pd.json_normalize(
                    data=request_data,
                    record_path=JSON_PATH_LISTS["data_base"]["record_path"],
                    meta=JSON_PATH_LISTS["data_base"]["meta"],
                )
            if datatype == "hourly":
                data = pd.json_normalize(
                    data=request_data,
                    record_path=JSON_PATH_LISTS["data_hour"]["record_path"],
                    meta=JSON_PATH_LISTS["data_hour"]["meta"],
                )

        else:
            data = pd.json_normalize(
                data=request_data,
                record_path=JSON_PATH_LISTS[folder]["record_path"],
                meta=JSON_PATH_LISTS[folder]["meta"],
            )

        for col in data.columns:
            if col not in list(HEADER_RENAME_LISTS[folder].keys()):
                data[col] = np.nan

    return data.rename(columns=HEADER_RENAME_LISTS[folder])


def build_dataframe(data: dict, header: list, datatype: str) -> pd.DataFrame:

    out_df = pd.DataFrame(columns=header)
    for i in range(len(data[:])):
        df = pd.DataFrame(data[i][datatype]["data"])

        df["id"] = data[i]["id"]

        for col in header:
            if col not in df.columns:
                df.insert(2, col, None)

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            out_df = pd.concat(
                [out_df, df], join="inner", ignore_index=True, sort=False
            )

        out_df["date"] = pd.to_datetime(out_df["date"], format="%Y-%m-%dT%H:%M:%SZ")

    return out_df


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


def add_poll_info(
    data: pd.DataFrame,
    site_info: pd.DataFrame,
    columns: list,
    new_col: dict = None,
) -> pd.DataFrame:

    for head in columns:
        data.insert(0, head, site_info[head].iloc[0])
    if new_col:
        for head in new_col:
            data.insert(0, head, new_col[head])
    return data


def mask_aorp(data):

    data["value"] = data.apply(
        lambda row: (
            np.nan if row["state"] not in ["A", "O", "R", "P"] else row["value"]
        ),
        axis=1,
    )
    return data[["id", "value", "unit"]]



def mask_duplicates(
    data: pd.DataFrame,
    site_name: str,
    poll_iso: str,
):
    if poll_iso == "24":
        data_out = data[data["id"].str.contains(f"PC{site_name[:2]}")]
    if poll_iso == "39":
        data_out = data[data["id"].str.contains(f"P2{site_name[:2]}")]
    if poll_iso == "68":
        for id in data.id.unique():
            if f"PM1{site_name[:2]}".lower() in str(id).lower():
                data_out = data[data["id"].str.contains(f"PM1{site_name[:2]}")]
                break
            else:
                data_out = data[data["id"] == data["id"].unique()[0]]
    return data_out
