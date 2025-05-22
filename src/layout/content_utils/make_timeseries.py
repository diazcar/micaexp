from src.fonctions import graph_title
from src.glob_vars import SEUILS, UNITS


from plotly import graph_objects as go


def make_timeseries(
    graph_data, color_map, aggregation, polluant, station_name=None
):
    timeseries_fig = go.Figure()
    y_max = graph_data.max().max()
    for col in graph_data.columns:
        timeseries_fig.add_trace(
            go.Scatter(
                y=graph_data[col],
                x=graph_data.index,
                line=dict(color=color_map[col]),
                name="Station" if col == "station" else col,
            )
        )
    if polluant in ["PM10", "PM2.5"]:
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
            timeseries_fig.add_annotation(
                x=graph_data.index[round(len(graph_data.index) * 0.1)],
                y=SEUILS[polluant]["FR"][seuil],
                text=seuil,
            )
    dtick = graph_data.index[1] - graph_data.index[0]
    timeseries_fig.update_layout(
        title=graph_title("timeseries", aggregation, polluant),
        title_x=0.5,
        xaxis=dict(
            dtick=dtick,
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
        yaxis_range=[0, y_max + y_max * 0.05],
    )
    return timeseries_fig
