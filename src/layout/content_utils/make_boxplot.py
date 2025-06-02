from src.utils.fonctions import graph_title
from src.utils.glob_vars import SEUILS, UNITS

from plotly import graph_objects as go


def make_boxplot(
    graph_data,
    color_map,
    aggregation,
    polluant,
    station_name=None,
    show_thresholds=False,
):
    # Handle empty data gracefully
    if graph_data.empty or len(graph_data.index) < 1:
        fig = go.Figure()
        fig.update_layout(
            title="Aucune donnée à afficher",
            title_x=0.5,
            plot_bgcolor="#f9f9f9",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    fig_boxplot = go.Figure()
    fig_boxplot.layout.xaxis2 = go.layout.XAxis(
        overlaying="x", range=[0, 1], showticklabels=False
    )
    for col in graph_data.columns:
        fig_boxplot.add_trace(
            go.Box(
                y=graph_data[col],
                name=station_name if col == "station" else col,
                line=dict(color=color_map[col]),
            )
        )
    # Add thresholds if requested
    if show_thresholds and polluant in ["PM10", "PM2.5"]:
        for i, seuil in enumerate(list(SEUILS[polluant]["FR"].keys())):
            seuil_value = SEUILS[polluant]["FR"][seuil]
            fig_boxplot.add_scatter(
                x=[0, 1],
                y=[seuil_value, seuil_value],
                mode="lines",
                xaxis="x2",
                showlegend=False,
                line=dict(dash="dash", color="firebrick", width=2),
            )
    fig_boxplot.update_layout(
        title=graph_title("boxplot", aggregation, polluant),
        title_x=0.5,
        yaxis=dict(
            title=f"{polluant} {UNITS[polluant]}",
            autorange=True,  # Enable autoscale for y-axis
        ),
        xaxis_title="",
        xaxis2_showticklabels=False,
        showlegend=False,
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(
            b=0,
            l=0,
            r=0,
            t=25,
        ),
        # yaxis_range removed for autoscale
    )
    return fig_boxplot
