from plotly import graph_objects as go


def make_map(graph_data, gdf, color_map, station_name):
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
        mapbox_style="satellite-streets",
        mapbox_accesstoken="pk.eyJ1IjoibHVjYXNoZWlucnkiLCJhIjoiY21hcGR0emloMGhhMTJpcjNobnlnNjg2YyJ9.SHuOyKk5vzAZm6896SdnYA",
        mapbox_zoom=6.5,
        mapbox_center=dict(lon=6, lat=44),
        autosize=True,
        margin=dict(t=0, b=0, l=5, r=0),
    )
    return fig_map
