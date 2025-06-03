from src.utils.fonctions import graph_title
from src.utils.glob_vars import SEUILS, UNITS

from plotly import graph_objects as go


def make_timeseries(
    graph_data,
    color_map,
    aggregation,
    polluant,
    station_name=None,
    show_thresholds=False,
):
    # Handle empty data gracefully
    if graph_data.empty or len(graph_data.index) < 2:
        fig = go.Figure()
        fig.update_layout(
            title="Aucune donnée à afficher",
            title_x=0.5,
            plot_bgcolor="#f9f9f9",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    timeseries_fig = go.Figure()
    for col in graph_data.columns:
        timeseries_fig.add_trace(
            go.Scatter(
                y=graph_data[col],
                x=graph_data.index,
                line=dict(color=color_map[col]),
                name=station_name if col == "station" else col,
            )
        )
    # Only show thresholds if requested
    if show_thresholds and polluant in ["PM10", "PM2.5"]:
        for i, seuil in enumerate(list(SEUILS[polluant]["FR"].keys())):
            timeseries_fig.add_trace(
                go.Scatter(
                    y=[SEUILS[polluant]["FR"][seuil]] * len(graph_data.index),
                    x=graph_data.index,
                    name=seuil,
                    line=dict(color="black", dash="dash"),
                    showlegend=False,
                )
            )
    # Remove manual dtick for automatic tick handling by Plotly
    timeseries_fig.update_layout(
        title=graph_title("timeseries", aggregation, polluant),
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
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5,
        ),
        margin=dict(
            b=0,
            l=0,
            r=0,
            t=60,
        ),
        # yaxis_range removed for autoscale
    )
    return timeseries_fig
