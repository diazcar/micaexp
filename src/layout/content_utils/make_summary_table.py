from src.utils.fonctions import get_stats

import pandas as pd


def make_summary_table(graph_data, hour_data, polluant, station_name):
    summary_dict = {
        "Nom": [],
        "Concentration moyenne (µg/m³)": [],
        "Min / Max (µg/m³)": [],
    }
    for i, col in enumerate(graph_data.columns):
        name = station_name if station_name and col == "station" else col
        stats = get_stats(
            hour_data=hour_data[[col]], minmax_data=hour_data[[col]], poll=polluant
        )
        (
            moyenne_periode,
            min_periode, 
            max_periode,
        ) = stats
        summary_dict["Nom"].append(name)
        summary_dict["Concentration moyenne (µg/m³)"].append(f"{moyenne_periode[0]:.0f}")
        summary_dict["Min / Max (µg/m³)"].append(
            f"{min_periode[0]:.0f} / {max_periode[0]:.0f}"
        )
    summary_df = pd.DataFrame(summary_dict)
    summary_df = (
        summary_df.set_index("Nom")
        .T.reset_index()
        .rename(columns={"index": "Statistiques"})
    )
    columns = [{"name": col, "id": col} for col in summary_df.columns]
    data = summary_df.to_dict("records")
    return columns, data
