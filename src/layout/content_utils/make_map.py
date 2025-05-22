from plotly import graph_objects as go
from src.fonctions import get_geoDF


def make_map(
    graph_data,
    color_map,
    polluant,
    start_date,
    end_date,
    station_name=None,
):

    gdf = get_geoDF(
        id_capteur=[
            int(col.split("_")[-1]) for col in graph_data.columns if col != "station"
        ],
        polluant=polluant,
        start_date=start_date,
        end_date=end_date,
        nom_station=station_name,
    )

    fig_map = go.Figure(layout=dict(height=600, width=800))
    capteur_cols = [col for col in graph_data.columns if col != "station"]
    for idx, cap_id in enumerate(capteur_cols):
        row = gdf.iloc[idx]
        color = color_map[cap_id]
        fig_map.add_trace(
            go.Scattermapbox(
                lat=[row.geometry.y],
                lon=[row.geometry.x],
                name=f"{cap_id}",
                mode="markers",
                marker=dict(size=15, color=color),
            )
        )
    if station_name and len(gdf) > len(capteur_cols):
        station_row = gdf.iloc[-1]
        fig_map.add_trace(
            go.Scattermapbox(
                lat=[station_row.geometry.y],
                lon=[station_row.geometry.x],
                name=station_name,
                mode="markers",
                marker=dict(size=15, color="firebrick"),
            )
        )
    fig_map.update_layout(
        mapbox_style="open-street-map",
        mapbox_zoom=6.5,
        mapbox_center=dict(lon=6, lat=44),
        autosize=True,
        margin=dict(t=0, b=0, l=5, r=0),
    )
    return fig_map
