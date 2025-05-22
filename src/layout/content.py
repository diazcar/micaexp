from dotenv import load_dotenv
from dash import html, dcc, Input, Output, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from src.fonctions import (
    get_geoDF,
    get_max,
    weekday_profile,
    get_color_map,
)
from src.glob_vars import COLORS
from src.layout.content_utils.make_24h_avg import make_24h_avg
from src.layout.content_utils.make_boxplot import make_boxplot
from src.layout.content_utils.make_corr_matrix import make_corr_matrix
from src.layout.content_utils.make_diurnal_cycle import make_diurnal_cycle
from src.layout.content_utils.make_map import make_map
from src.layout.content_utils.make_summary_table import make_summary_table
from src.layout.content_utils.make_timeseries import make_timeseries
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
    Output("timeseries", "figure"),
    Output("diurnal_cycle_workweek", "figure"),
    Output("diurnal_cycle_weekend", "figure"),
    Output("boxplot", "figure"),
    Output("correlation_matrix", "figure"),
    Output("summary_table", "columns"),
    Output("summary_table", "data"),
    Output("avg24h", "figure"),
    Output("map", "figure"),
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
    # REMOVE this watermark definition:
    # watermark = [
    #     dict(
    #         source="./assets/logo_atmosud_inspirer_web.png",
    #         xref="paper",
    #         yref="paper",
    #         x=0.5,
    #         y=0.2,
    #         sizex=0.5,
    #         sizey=0.5,
    #         xanchor="center",
    #         yanchor="bottom",
    #         opacity=0.08,
    #     )
    # ]

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
        if micro_col_name not in capteur_hour_data.columns:
            capteur_hour_data[micro_col_name] = np.nan
        capteur_hour_dfs.append(capteur_hour_data[[micro_col_name]])

    if station_name and station_quart_data is not None:
        quart_data = pd.concat(
            [station_quart_data[station_col_name]] + capteur_quart_dfs, axis=1
        )
        hour_data = pd.concat(
            [station_hour_data[station_col_name]] + capteur_hour_dfs, axis=1
        )
    else:
        if not capteur_quart_dfs:
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

    color_map = get_color_map(graph_data.columns)

    week_diurnal_cycle_data = weekday_profile(
        data=graph_data,
        week_section="workweek",
    )
    wend_diurnal_cycle_data = weekday_profile(
        data=graph_data,
        week_section="weekend",
    )

    gdf = get_geoDF(
        id_capteur=[
            int(col.split("_")[-1]) for col in graph_data.columns if col != "station"
        ],
        polluant=polluant,
        start_date=start_date,
        end_date=end_date,
        nom_station=station_name,
    )

    # When calling your graph functions, REMOVE the watermark argument:
    timeseries_fig = make_timeseries(
        graph_data, color_map, aggregation, polluant, station_name
    )
    week_diurnal_cycle_fig = make_diurnal_cycle(
        week_diurnal_cycle_data, color_map, polluant, aggregation, "Profil journalier en semaine"
    )
    wend_diurnal_cycle_fig = make_diurnal_cycle(
        wend_diurnal_cycle_data, color_map, polluant, aggregation, "Profil journalier en week-end"
    )
    fig_boxplot = make_boxplot(
        graph_data, color_map, aggregation, polluant, station_name
    )
    fig_corr = make_corr_matrix(graph_data)
    columns, data = make_summary_table(graph_data, hour_data, polluant, station_name)
    fig_24h_avg = make_24h_avg(
        graph_data, color_map, aggregation, polluant, station_name
    )
    fig_map = make_map(graph_data, gdf, color_map, station_name)

    return (
        timeseries_fig,
        week_diurnal_cycle_fig,
        wend_diurnal_cycle_fig,
        fig_boxplot,
        fig_corr,
        columns,
        data,
        fig_24h_avg,
        fig_map,
    )
