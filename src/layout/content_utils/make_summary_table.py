from src.fonctions import get_stats
from src.glob_vars import SEUILS


import pandas as pd


def make_summary_table(graph_data, hour_data, polluant, station_name):
    summary_dict = {
        "Nom": [],
        "Moyenne période (µg/m³)": [],
        "Min / Max horaire (µg/m³)": [],
        f"Dépassements seuil info ({SEUILS[polluant]['FR']['seuil_information']} µg/m³/24h)": [],
        f"Dépassements seuil alerte ({SEUILS[polluant]['FR']['seuil_alerte']} µg/m³/24h)": [],
    }
    for i, col in enumerate(graph_data.columns):
        name = "Station" if station_name and col == "station" else col
        stats = get_stats(
            hour_data=hour_data[[col]], minmax_data=hour_data[[col]], poll=polluant
        )
        (
            count_seuil_information,
            count_seuil_alert,
            moyenne_periode,
            min_periode,
            max_periode,
            seuil_information,
            seuil_alert,
        ) = stats
        summary_dict["Nom"].append(name)
        summary_dict["Moyenne période (µg/m³)"].append(f"{moyenne_periode[0]:.0f}")
        summary_dict["Min / Max horaire (µg/m³)"].append(
            f"{min_periode[0]:.0f} / {max_periode[0]:.0f}"
        )
        summary_dict[f"Dépassements seuil info ({seuil_information} µg/m³/24h)"].append(
            f"{count_seuil_information[0]}"
        )
        summary_dict[f"Dépassements seuil alerte ({seuil_alert} µg/m³/24h)"].append(
            f"{count_seuil_alert[0]}"
        )
    summary_df = pd.DataFrame(summary_dict)
    summary_df = (
        summary_df.set_index("Nom")
        .T.reset_index()
        .rename(columns={"index": "Statistique"})
    )
    columns = [{"name": col, "id": col} for col in summary_df.columns]
    data = summary_df.to_dict("records")
    return columns, data
