from src.glob_vars import UNITS


from plotly import graph_objects as go
from src.fonctions import weekday_profile


def make_diurnal_cycle(
    graph_data, color_map, polluant, aggregation, title, week_section="workweek"
):
    # Compute the diurnal cycle profile inside the function
    diurnal_data = weekday_profile(
        data=graph_data,
        week_section=week_section,
    )
    dcycle_xticks_div = 2 if aggregation == "quart-horaire" else 1
    y_max = diurnal_data.max().max()
    fig = go.Figure()
    for col in diurnal_data.columns:
        fig.add_trace(
            go.Scatter(
                y=diurnal_data[col],
                x=diurnal_data.index,
                line=dict(color=color_map.get(col, None)),
                name="Station" if col == "station" else col,
            )
        )
    fig.update_layout(
        title=title,
        title_x=0.5,
        xaxis=dict(
            nticks=round(len(diurnal_data.index) / dcycle_xticks_div),
            tick0=diurnal_data.index[1],
            tickformat="%H:%M",
            tickangle=90,
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
        yaxis_range=[0, y_max],
    )
    return fig
