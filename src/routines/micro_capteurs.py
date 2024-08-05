import requests
import pandas as pd

KEYS = {
    'campagnes': 'capteurs/campagnes',
    'mesures': 'capteurs/mesures',
    'sites': 'capteurs/sites'
}

APIS_URLS = {
    'observations': 'https://api.atmosud.org/observations',
}

ISO = {
    'PM10': '24',
    'PM2.5': '39',
    'PM1': '68',
}

JSON_PATH_LIST = {
    'sites': {
        'record_path': None,
        'meta': [
            "id_site",
            "nom_site",
            "type_site",
            "influence",
            "lon",
            "lat",
            "code_station_commun",
            "date_debut_site",
            "date_fin_site",
            "alti_mer",
            "alti_sol",
            "id_campagne",
            "nom_campagne",
            "id_capteur",
            "marque_capteur",
            "modele_capteur",
            "variables"
        ]
    },
    'mesures': {
        'record_path': None,
        'meta': [  
            "id_site",
            "time",
            "nom_site",
            "variable",
            "lat",
            "lon",
            "valeur",
            "valeur_ref",
            "code_etat",
            "unite"
            ],
    },

}


def make_record_time(
        data: pd.DataFrame,
        folder_key: str,
):
    if folder_key == 'mesures':
        data['time'] = pd.to_datetime(
            data['time'],
            format="%Y-%m-%dT%H:%M:%SZ"
            )
        data.set_index('time', inplace=True)


def add_custom_columns(
        data: pd.DataFrame,
        folder_key: str,
) -> pd.DataFrame:
    if folder_key == 'sites':
        data['site_plus_capteur'] = data.apply(
            lambda row: f'{row.nom_site} - {row.id_site} ({row.id_capteur})',
            axis=1
            )


def get_site_info(
    col_key: str,
    search_key: str,
    col_target: str,
):
    info = CAPTEUR_SITE_INFO[
        CAPTEUR_SITE_INFO[col_key] == search_key
            ][col_target].values[0]

    return info


def request_api_observations(

        folder_key: str,
        api_url: str = 'observations',
        format: str = "json",
        download: str = 'false',
        start_date: str = None,
        end_date: str = None,
        id_campagne: int = None,
        nom_campagne: str = None,
        id_site: int = None,
        nom_site: str = None,
        id_capteur: int = None,
        id_variable: str = None,
        aggregation: str = 'horaire',
        nb_dec: int = None
) -> pd.DataFrame:

    if folder_key == 'sites':
        url = "".join(
            [
                f"{APIS_URLS[api_url]}/",
                f"{KEYS[folder_key]}?",
                f"id_variable={id_variable}&",
                f"format={format}&",
                f"download={download}&",
            ]
        )
        if nom_site:
            url += f"nom_site={nom_site}&"

    if folder_key == 'mesures':
        url = "".join(
            [
                f"{APIS_URLS[api_url]}/",
                f"{KEYS[folder_key]}?",
                f"debut={start_date}&",
                f"fin={end_date}&",
                f"id_site={id_site}&",
                f"format={format}&",
                f"download={download}&",
                f"aggregation={aggregation}&",
                f"nb_dec={nb_dec}&"
            ]
        )

    reponse = requests.get(
        url,
    ).json()
    data = pd.json_normalize(
        data=reponse,
        # record_path=JSON_PATH_LIST[folder_key]['record_path'],
        # meta=JSON_PATH_LIST[folder_key]['meta'],
    )
    add_custom_columns(data, folder_key)
    make_record_time(data, folder_key)

    return data


CAPTEUR_SITE_INFO = request_api_observations(
    folder_key='sites',
    format='json',
    download='false',
)
