import datetime as dt
import pandas as pd

TIME_NOW = dt.datetime.today()

PHYSICALS = pd.read_csv(
            "./data/physicals.csv"
        ).set_index('id').to_dict('index')

UNITS = {
    'PM10': 'µg/m³',
    'PM2.5': 'µg/m³',
    'PM1': 'µg/m³',
}

COLORS = {
    'lines': {
        'capteur': '#FBB911',  # R : 251 V : 185 B : 17
        'station': 'blue',
    },
    'markers': {
        'capteur': '#FBB911',  # R : 251 V : 185 B : 17
        'station': 'blue',
    },
}
SEUILS = {
    'PM10': {
        'FR': {
            'seuil_information': 50,
            'seuil_alerte': 80,
        #     'valeur_limite_moy_annuelle': 20,
        #     'valeur_cible_moy_jour': 20,
        # },
        # 'UE': {
        #     'valeur_limite_moy_annuelle': 40,
        #     'valeur_limite_moy_jour': 50,
        # },
        # 'OMS': {
        #     'valeur_limite_moy_annuelle': 15,
        #     'valeur_cible_moy_jour': 45,
        }
    },

    'PM2.5': {
        'FR': {
            'seuil_information': 15,
            'seuil_alerte': 25,
        #     'valeur_limite_moy_annuelle': 20,
        #     'valeur_cible_moy_jour': 20,
        # },
        # 'UE': {
        #     'valeur_limite_moy_annuelle': 25,
        #     'valeur_cible_moy_jour': 20,
        # },
        # 'OMS': {
        #     'valeur_limite_moy_annuelle': 5,
        #     'valeur_cible_moy_jour': 15,
        },
    },

    'PM1': {
        'FR': {
            'seuil_information': "-",
            'seuil_alerte': "-",
        #     'valeur_limite_moy_annuelle': 20,
        #     'valeur_cible_moy_jour': 20,
        # },
        # 'UE': {
        #     'valeur_limite_moy_annuelle': 25,
        #     'valeur_cible_moy_jour': 20,
        # },
        # 'OMS': {
        #     'valeur_limite_moy_annuelle': 5,
        #     'valeur_cible_moy_jour': 15,
        },
    },
}
