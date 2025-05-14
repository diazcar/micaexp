from dotenv import load_dotenv
from dash import html, dcc, Input, Output, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
from plotly import graph_objects as go
import numpy as np
from src.fonctions import (
    get_geoDF,
    get_max,
    get_stats,
    graph_title,
    weekday_profile,
    get_color_map,
)
from src.glob_vars import COLORS, SEUILS, UNITS
from src.layout.styles import CONTENT_STYLE
from maindash import app
from src.routines.microspot_api import request_microspot
from src.routines.xair import request_xr, wrap_xair_request, ISO
import plotly.colors

load_dotenv()


def get_content():
    return html.Div(
        [
            dcc.Loading(
                id="loading",
                children=[
                    html.H1(id="title_layout"),
                    html.Br(),
                    dash_table.DataTable(
                        id="summary_table",
                        columns=[],  # Will be set dynamically
                        data=[],  # Will be set dynamically
                        style_table={"overflowX": "auto"},
                        style_cell={"textAlign": "center"},
                    ),
                    html.Br(),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dcc.Graph(
                                        figure={},
                                        id="timeseries",
                                    ),
                                ],
                                width=12,
                            ),
                        ]
                    ),
                    html.Br(),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dcc.Graph(
                                        figure={},
                                        id="diurnal_cycle_workweek",
                                    )
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    dcc.Graph(
                                        figure={},
                                        id="diurnal_cycle_weekend",
                                    )
                                ],
                                width=6,
                            ),
                        ]
                    ),
                    html.Br(),
                    # dbc.Row([
                    #     dbc.Col([
                    #         dcc.Graph(
                    #             figure={},
                    #             id="diurnal_cycle_weekend",
                    #             style=dict(
                    #                 height='30vh'
                    #                 )
                    #             )
                    #         ], width=12),
                    #     ]),
                    html.Br(),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Br(),
                                    html.Br(),
                                    html.Br(),
                                    html.Br(),
                                    dcc.Graph(figure={}, id="boxplot"),
                                    dcc.Graph(
                                        figure={}, id="avg24h"
                                    ),  # <-- Add this line
                                    dcc.Graph(
                                        figure={}, id="correlation_matrix"
                                    ),  # Add this line
                                    dcc.Graph(
                                        figure={}, id="map"
                                    ),  # Map now below the boxplot
                                ],
                                width=12,
                            ),
                            # Optionally, you can remove the second column or leave it empty
                            dbc.Col(
                                [],
                                width=12,
                            ),
                        ]
                    ),
                    html.Hr(),
                    html.Img(
                        src="assets/valeurs_de_reference.png", style={"height": "70%"}
                    ),
                    html.H6(
                        [
                            html.B("Seuil d’information "),
                            "- Niveau de concentration sur 24h au delà duquel des informations sont diffusées aux personnes sensibles",
                            html.Br(),
                            html.B("Seuil d’alerte "),
                            "- Niveau de concentration sur 24h au delà duquel il y a un risque pour la santé justifiant de mesures d'urgence",
                            html.Br(),
                            html.B("Ligne directrice (LD) "),
                            "- Valeur recommandée par l'Organisation Mondiale de la Santé",
                            html.Br(),
                            html.B("Valeur cible (VC) "),
                            "- Niveau de concentration à atteindre dans un délai donné",
                            html.Br(),
                            html.B("Valeur limite (VL) "),
                            "-Niveau réglementaire de concentration à ne pas dépasser",
                            html.Br(),
                            html.B("Objectif qualité (OQ) "),
                            "-Niveau de concentration à attendre à long terme",
                            html.Br(),
                        ]
                    ),
                ],
            )
        ],
        style=CONTENT_STYLE,
    )


@app.callback(
    Output("title_layout", "children"),
    Input("polluant_dropdown", "value"),
)
def build_title(poll: str):
    return html.B(
        html.Center(f"Données {poll}"),
    )


@app.callback(
    # Output('map_img', 'src'),
    Output("map", "figure"),
    Input("micro_capteur_sites_dropdown", "value"),
    Input("polluant_dropdown", "value"),
    Input("my-date-picker-range", "start_date"),
    Input("my-date-picker-range", "end_date"),
    Input("station_xair_dropdown", "value"),
)
def generate_map(
    site_plus_capteur: list,
    polluant: str,
    start_date: str,
    end_date: str,
    station_name: str,
):
    # Prepare lists for names and ids
    cap_names = []
    cap_ids = []
    for cap in site_plus_capteur:
        name, cid = cap.rsplit(" - ", 1)
        cap_names.append(name)
        cap_ids.append(int(cid))

    # Get geo data for all sensors and station
    gdf = get_geoDF(
        id_capteur=cap_ids,  # Assuming get_geoDF can handle a list of ids
        polluant=polluant,
        start_date=start_date,
        end_date=end_date,
        nom_station=station_name,
    )

    fig_map = go.Figure(layout=dict(height=600, width=800))

    # Add microcapteur markers
    for i, cap_id in enumerate(cap_ids):
        row = gdf.iloc[i]
        fig_map.add_trace(
            go.Scattermapbox(
                lat=[row.geometry.y],
                lon=[row.geometry.x],
                name=f"{cap_names[i]}",
                mode="markers",
                marker=dict(size=15, color=COLORS["markers"]["capteur"]),
            )
        )

    # Add station marker only if station_name is provided and present in gdf
    if station_name and len(gdf) > len(cap_ids):
        station_row = gdf.iloc[-1]
        fig_map.add_trace(
            go.Scattermapbox(
                lat=[station_row.geometry.y],
                lon=[station_row.geometry.x],
                name=station_name,
                mode="markers",
                marker=dict(size=15, color=COLORS["markers"]["station"]),
            )
        )

    fig_map.update_layout(
        images=[
            dict(
                source="./assets/logo_atmosud_inspirer_web.png",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.2,
                sizex=0.5,
                sizey=0.5,
                xanchor="center",
                yanchor="bottom",
                opacity=0.08,
            )
        ],
        mapbox_style="open-street-map",
        mapbox_zoom=6.5,
        mapbox_center=dict(lon=6, lat=44),
        autosize=True,
        margin=dict(t=0, b=0, l=5, r=0),
    )

    return fig_map


@app.callback(
    Output("timeseries", "figure"),
    Output("diurnal_cycle_workweek", "figure"),
    Output("diurnal_cycle_weekend", "figure"),
    Output("boxplot", "figure"),
    Output("correlation_matrix", "figure"),  # Add this line
    Output("summary_table", "columns"),
    Output("summary_table", "data"),
    Output("avg24h", "figure"),
    Input("my-date-picker-range", "start_date"),
    Input("my-date-picker-range", "end_date"),
    Input("micro_capteur_sites_dropdown", "value"),
    Input("polluant_dropdown", "value"),
    Input("station_xair_dropdown", "value"),
    Input("time_step_dropdown", "value"),
)
def build_graphs(
    start_date: np.datetime64,
    end_date: np.datetime64,
    site_plus_capteur: list,
    polluant: str,
    station_name: str = None,
    aggregation: str = "quart-horaire",
):
    watermark = [
        dict(
            source="./assets/logo_atmosud_inspirer_web.png",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.2,
            sizex=0.5,
            sizey=0.5,
            xanchor="center",
            yanchor="bottom",
            opacity=0.08,
        )
    ]

    # Fetch station data only if station_name is provided
    if station_name:
        station_quart_data = wrap_xair_request(
            fromtime=start_date,
            totime=end_date,
            keys="data",
            sites=station_name,
            physicals=ISO[polluant],
            datatype="quart-horaire",
        )
        station_hour_data = wrap_xair_request(
            fromtime=start_date,
            totime=end_date,
            keys="data",
            sites=station_name,
            physicals=ISO[polluant],
            datatype="horaire",
        )
        station_col_name = "station"
        station_quart_data = station_quart_data.rename(
            columns={"value": station_col_name}
        )
        station_hour_data = station_hour_data.rename(
            columns={"value": station_col_name}
        )
    else:
        station_quart_data = None
        station_hour_data = None
        station_col_name = None

    # Prepare dataframes for all selected sensors
    capteur_quart_dfs = []
    capteur_hour_dfs = []

    for capteur in site_plus_capteur:
        cap_name, cap_id = capteur.rsplit(" - ", 1)
        cap_id = int(cap_id)
        micro_col_name = f"microcapteur_{cap_id}"

        capteur_quart_data = request_microspot(
            observationTypeCodes=[ISO[polluant]],
            devices=[cap_id],
            aggregation="quart-horaire",
            dateRange=[f"{start_date}T00:00:00+00:00", f"{end_date}T00:00:00+00:00"],
        )
        capteur_quart_data = capteur_quart_data[
            capteur_quart_data.isoCode == ISO[polluant]
        ]
        capteur_quart_data = capteur_quart_data.rename(
            columns={"valueRaw": micro_col_name}
        )
        capteur_quart_dfs.append(capteur_quart_data[[micro_col_name]])

        capteur_hour_data = request_microspot(
            observationTypeCodes=[ISO[polluant]],
            devices=[cap_id],
            aggregation="horaire",
            dateRange=[f"{start_date}T00:00:00+00:00", f"{end_date}T00:00:00+00:00"],
        )
        capteur_hour_data = capteur_hour_data[
            capteur_hour_data.isoCode == ISO[polluant]
        ]
        capteur_hour_data = capteur_hour_data.rename(
            columns={"valueModified": micro_col_name}
        )
        # Patch: ensure column exists, else fill with NaN
        if micro_col_name not in capteur_hour_data.columns:
            capteur_hour_data[micro_col_name] = np.nan
        capteur_hour_dfs.append(capteur_hour_data[[micro_col_name]])

    # Concatenate all microcapteur columns with station data if present
    if station_name and station_quart_data is not None:
        quart_data = pd.concat(
            [station_quart_data[station_col_name]] + capteur_quart_dfs, axis=1
        )
        hour_data = pd.concat(
            [station_hour_data[station_col_name]] + capteur_hour_dfs, axis=1
        )
    else:
        if not capteur_quart_dfs:
            # Create empty DataFrame with date index if possible
            date_index = pd.date_range(start=start_date, end=end_date, freq="15min")
            quart_data = pd.DataFrame(index=date_index)
        else:
            quart_data = pd.concat(capteur_quart_dfs, axis=1)

        if not capteur_hour_dfs:
            date_index = pd.date_range(start=start_date, end=end_date, freq="H")
            hour_data = pd.DataFrame(index=date_index)
        else:
            hour_data = pd.concat(capteur_hour_dfs, axis=1)

    graph_data = hour_data if aggregation == "horaire" else quart_data

    # Diurnal cycle and color map
    if aggregation == "quart-horaire":
        dcycle_xticks_div = 2
    else:
        dcycle_xticks_div = 1

    color_map = get_color_map(graph_data.columns)

    # -------------------------------------
    #           DIURNAL CYCLE DATA
    # -------------------------------------

    week_diurnal_cycle_data = weekday_profile(
        data=graph_data,
        week_section="workweek",
    )
    wend_diurnal_cycle_data = weekday_profile(
        data=graph_data,
        week_section="weekend",
    )

    color_map = get_color_map(graph_data.columns)

    # -------------------------------------
    #  CAPTEUR             TIMESERIES
    # -------------------------------------
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
        images=watermark,
        xaxis=dict(
            dtick=dtick,
            showgrid=True,
            gridcolor="#cccccc",
            gridwidth=1.5,  # <--- increased gridwidth
            zeroline=False,
        ),
        yaxis=dict(
            title=f"{polluant} {UNITS[polluant]}",
            showgrid=True,
            gridcolor="#cccccc",
            gridwidth=1.5,  # <--- increased gridwidth
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
            t=60,  # <-- Increased top margin for title visibility
        ),
        yaxis_range=[0, y_max + y_max * 0.05],
    )
    # ---------------------------------------------------
    # CAPTEUR         WEEKDAY DIURNAL CYCLE
    # ---------------------------------------------------
    y_max = get_max(week_diurnal_cycle_data, wend_diurnal_cycle_data)

    week_diurnal_cycle_fig = go.Figure()
    for col in week_diurnal_cycle_data.columns:
        week_diurnal_cycle_fig.add_trace(
            go.Scatter(
                y=week_diurnal_cycle_data[col],
                x=week_diurnal_cycle_data.index,
                line=dict(color=color_map.get(col, None)),
                name="Station" if col == "station" else col,
            )
        )

    week_diurnal_cycle_fig.update_layout(
        title="Profil journalier en semaine",
        title_x=0.5,
        images=watermark,
        xaxis=dict(
            nticks=round(len(week_diurnal_cycle_data.index) / dcycle_xticks_div),
            tick0=week_diurnal_cycle_data.index[1],
            tickformat="%H:%M",
            tickangle=90,
            showgrid=True,
            gridcolor="#cccccc",
            gridwidth=1.5,  # <--- increased gridwidth
            zeroline=False,
        ),
        yaxis=dict(
            title=f"{polluant} {UNITS[polluant]}",
            showgrid=True,
            gridcolor="#cccccc",
            gridwidth=1.5,  # <--- increased gridwidth
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
            t=60,  # Increased top margin for title visibility
        ),
        yaxis_range=[0, y_max],
    )

    # ---------------------------------------------------
    #         WENDDAY DIURNAL CYCLE
    # ---------------------------------------------------
    wend_diurnal_cycle_fig = go.Figure()

    for col in wend_diurnal_cycle_data.columns:
        wend_diurnal_cycle_fig.add_trace(
            go.Scatter(
                y=wend_diurnal_cycle_data[col],
                x=wend_diurnal_cycle_data.index,
                line=dict(color=color_map.get(col, None)),
                name="Station" if col == "station" else col,
            )
        )

    wend_diurnal_cycle_fig.update_layout(
        title="Profil journalier en week-end",
        title_x=0.5,
        images=watermark,
        xaxis=dict(
            tick0=week_diurnal_cycle_data.index[1],
            nticks=round(len(week_diurnal_cycle_data.index) / dcycle_xticks_div),
            tickformat="%H:%M",
            tickangle=90,
            showgrid=True,
            gridcolor="#cccccc",
            gridwidth=1.5,  # <--- increased gridwidth
            zeroline=False,
        ),
        yaxis=dict(
            title=f"{polluant} {UNITS[polluant]}",
            showgrid=True,
            gridcolor="#cccccc",
            gridwidth=1.5,  # <--- increased gridwidth
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
            t=60,  # Increased top margin for title visibility
        ),
        yaxis_range=[0, y_max],
    )

    # ---------------------------------------------------
    #        BOXPLOT CAPTEUR
    # ---------------------------------------------------
    fig_boxplot = go.Figure()
    y_max = graph_data.max().max()
    fig_boxplot.layout.xaxis2 = go.layout.XAxis(
        overlaying="x", range=[0, 1], showticklabels=False
    )

    for col in graph_data.columns:
        fig_boxplot.add_trace(
            go.Box(
                y=graph_data[col],
                name="Station" if col == "station" else col,
                line=dict(color=color_map[col]),
            )
        )

    if polluant in ["PM10", "PM2.5"]:
        for i, seuil in enumerate(list(SEUILS[polluant]["FR"].keys())):
            seuil_value = SEUILS[polluant]["FR"][seuil]
            fig_boxplot.add_annotation(
                x=0.2, y=SEUILS[polluant]["FR"][seuil], text=seuil, axref="pixel"
            )

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
        images=watermark,
        yaxis=dict(
            title=f"{polluant} {UNITS[polluant]}"
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
        yaxis_range=[0, 100],
        # yaxis_range=[0, y_max+y_max*.05]
    )

    # Compute correlation matrix
    corr_matrix = graph_data.corr()

    # Create heatmap figure
    fig_corr = go.Figure(
        data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale="Viridis",
            zmin=-1,
            zmax=1,
            colorbar=dict(title="Correlation"),
        )
    )
    fig_corr.update_layout(
        title="Matrice de corrélation",
        title_x=0.5,
        margin=dict(t=60, b=40, l=0, r=0),
        xaxis=dict(
            tickangle=45,
            showgrid=True,
            gridcolor="#cccccc",
            gridwidth=1.5,  # <--- increased gridwidth
            zeroline=False,
        ),
        yaxis=dict(
            autorange="reversed",
            showgrid=True,
            gridcolor="#cccccc",
            gridwidth=1.5,  # <--- increased gridwidth
            zeroline=False,
        ),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # ---------------------------------------------------
    #        24H ROLLING MEAN (24h averaged lines)
    # ---------------------------------------------------
    fig_24h_avg = go.Figure()
    if not graph_data.empty:
        if aggregation == "horaire":
            window = 24
        else:  # quart-horaire
            window = 96
        rolling_24h = graph_data.rolling(window=window, min_periods=1).mean()
        for col in rolling_24h.columns:
            fig_24h_avg.add_trace(
                go.Scatter(
                    y=rolling_24h[col],
                    x=rolling_24h.index,
                    mode="lines",
                    line=dict(color=color_map.get(col, None), dash="solid"),
                    name="Station" if station_name and col == "station" else col,
                )
            )
        # Add seuil lines if relevant
        if polluant in ["PM10", "PM2.5"]:
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
                fig_24h_avg.add_annotation(
                    x=rolling_24h.index[round(len(rolling_24h.index) * 0.1)],
                    y=seuil_value,
                    text=seuil,
                )
    fig_24h_avg.update_layout(
        title="Moyenne glissante 24h",
        title_x=0.5,
        images=watermark,
        xaxis=dict(
            dtick=graph_data.index[1] - graph_data.index[0],
            showgrid=True,
            gridcolor="#cccccc",
            gridwidth=1.5,  # <--- increased gridwidth
            zeroline=False,
        ),
        yaxis=dict(
            title=f"{polluant} {UNITS[polluant]}",
            showgrid=True,
            gridcolor="#cccccc",
            gridwidth=1.5,  # <--- increased gridwidth
            zeroline=False,
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

    # ---------------------------------------------------
    #         SEUILS DE REFERENCE INFO
    # ---------------------------------------------------
    (
        count_seuil_information,
        count_seuil_alert,
        moyenne_periode,
        min_periode,
        max_periode,
        seuil_information,
        seuil_alert,
    ) = get_stats(hour_data=hour_data, minmax_data=hour_data, poll=polluant)

    # Build a summary DataFrame for all sensors and the station
    summary_dict = {
        "Nom": [],
        "Moyenne période (µg/m³)": [],
        "Min / Max horaire (µg/m³)": [],
        f"Dépassements seuil info ({seuil_information} µg/m³/24h)": [],
        f"Dépassements seuil alerte ({seuil_alert} µg/m³/24h)": [],
    }

    # For each microcapteur
    for i, col in enumerate(graph_data.columns):
        name = "Station" if station_name and col == "station" else col
        stats = get_stats(
            hour_data=hour_data[[col]], minmax_data=hour_data[[col]], poll=polluant
        )
        (
            count_seuil_information,
            count_seuil_alert,
            moyenne_periode,
            min_periode,
            max_periode,
            seuil_information,
            seuil_alert,
        ) = stats

        summary_dict["Nom"].append(name)
        summary_dict["Moyenne période (µg/m³)"].append(f"{moyenne_periode[0]:.0f}")
        summary_dict["Min / Max horaire (µg/m³)"].append(
            f"{min_periode[0]:.0f} / {max_periode[0]:.0f}"
        )
        summary_dict[f"Dépassements seuil info ({seuil_information} µg/m³/24h)"].append(
            f"{count_seuil_information[0]}"
        )
        summary_dict[f"Dépassements seuil alerte ({seuil_alert} µg/m³/24h)"].append(
            f"{count_seuil_alert[0]}"
        )

    summary_df = pd.DataFrame(summary_dict)
    summary_df = (
        summary_df.set_index("Nom")
        .T.reset_index()
        .rename(columns={"index": "Statistique"})
    )

    columns = [{"name": col, "id": col} for col in summary_df.columns]
    data = summary_df.to_dict("records")

    return (
        timeseries_fig,
        week_diurnal_cycle_fig,
        wend_diurnal_cycle_fig,
        fig_boxplot,
        fig_corr,  # Add this to the return
        columns,
        data,
        fig_24h_avg,  # Add this to the return
    )
