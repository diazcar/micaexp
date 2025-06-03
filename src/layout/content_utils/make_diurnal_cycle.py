from src.utils.glob_vars import UNITS, SEUILS
from plotly import graph_objects as go
from src.utils.fonctions import weekday_profile


def make_diurnal_cycle(
    graph_data,
    color_map,
    polluant,
    aggregation,
    title,
    week_section="workweek",
    station_name=None,
    show_thresholds=False,
):
    # Compute the diurnal cycle profile inside the function
    diurnal_data = weekday_profile(
        data=graph_data,
        week_section=week_section,
    )

    # Handle empty diurnal_data gracefully
    if diurnal_data.empty or len(diurnal_data.index) < 2:
        fig = go.Figure()
        fig.update_layout(
            title="Aucune donnée à afficher",
            title_x=0.5,
            plot_bgcolor="#f9f9f9",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    dcycle_xticks_div = 2 if aggregation == "quart-horaire" else 1
    fig = go.Figure()
    for col in diurnal_data.columns:
        fig.add_trace(
            go.Scatter(
                y=diurnal_data[col],
                x=diurnal_data.index,
                line=dict(color=color_map.get(col, None)),
                name=station_name if col == "station" else col,
            )
        )
    # Add seuils if requested and polluant is PM10 or PM2.5
    if show_thresholds and polluant in ["PM10", "PM2.5"]:
        for i, seuil in enumerate(list(SEUILS[polluant]["FR"].keys())):
            fig.add_trace(
                go.Scatter(
                    y=[SEUILS[polluant]["FR"][seuil]] * len(diurnal_data.index),
                    x=diurnal_data.index,
                    name=seuil,
                    line=dict(color="black", dash="dash"),
                    showlegend=False,
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
    return fig
