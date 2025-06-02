from src.utils.glob_vars import SEUILS, UNITS
from plotly import graph_objects as go


def make_24h_avg(
    graph_data,
    color_map,
    aggregation,
    polluant,
    station_name=None,
    show_thresholds=False,
):
    fig_24h_avg = go.Figure()
    if graph_data.empty or len(graph_data.index) < 2:
        fig_24h_avg.update_layout(
            title="Aucune donnée à afficher",
            title_x=0.5,
            plot_bgcolor="#f9f9f9",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        return fig_24h_avg

    window = 24 if aggregation == "horaire" else 96
    rolling_24h = graph_data.rolling(window=window, min_periods=1).mean()
    for col in rolling_24h.columns:
        fig_24h_avg.add_trace(
            go.Scatter(
                y=rolling_24h[col],
                x=rolling_24h.index,
                mode="lines",
                line=dict(color=color_map.get(col, None), dash="solid"),
                name=station_name if station_name and col == "station" else col,
            )
        )
    # Add thresholds if requested
    if show_thresholds and polluant in ["PM10", "PM2.5"]:
        for seuil in SEUILS[polluant]["FR"]:
            seuil_value = SEUILS[polluant]["FR"][seuil]
            fig_24h_avg.add_trace(
                go.Scatter(
                    y=[seuil_value] * len(rolling_24h.index),
                    x=rolling_24h.index,
                    name=seuil,
                    line=dict(color="black", dash="dash"),
                    showlegend=False,
                )
            )
    fig_24h_avg.update_layout(
        title="Moyenne glissante 24h",
        title_x=0.5,
        xaxis=dict(
            showgrid=True,
            gridcolor="#cccccc",
            gridwidth=1.5,
            zeroline=False,
        ),
        yaxis=dict(
            title=f"{polluant} {UNITS[polluant]}",
            showgrid=True,
            gridcolor="#cccccc",
            gridwidth=1.5,
            zeroline=False,
            autorange=True,  # Enable autoscale for y-axis
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5,
        ),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(b=0, l=0, r=0, t=60),
    )
    return fig_24h_avg
