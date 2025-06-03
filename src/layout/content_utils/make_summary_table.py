import pandas as pd


def make_summary_table(graph_data, station_name):
    NAME = "Nom"
    MEAN = "Concentration moyenne (µg/m³)"
    MINMAX = "Min / Max (µg/m³)"
    Q90 = "Quantile 90 (µg/m³)"

    summary_dict = {
        NAME: [],
        MEAN: [],
        MINMAX: [],
        Q90: [],
    }
    for col in graph_data.columns:
        name = station_name if station_name and col == "station" else col
        col_data = graph_data[col]
        mean_val = col_data.mean()
        min_val = col_data.min()
        max_val = col_data.max()
        q90_val = col_data.quantile(0.9)
        summary_dict[NAME].append(name)
        summary_dict[MEAN].append(f"{mean_val:.0f}")
        summary_dict[MINMAX].append(f"{min_val:.0f} / {max_val:.0f}")
        summary_dict[Q90].append(f"{q90_val:.0f}")
    summary_df = pd.DataFrame(summary_dict)
    summary_df = (
        summary_df.set_index(NAME)
        .T.reset_index()
        .rename(columns={"index": "Statistiques"})
    )
    columns = [{"name": col, "id": col} for col in summary_df.columns]
    data = summary_df.to_dict("records")
    return columns, data
