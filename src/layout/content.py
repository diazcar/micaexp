from dotenv import load_dotenv
from dash import html, dcc, Input, Output, dash_table
import dash_bootstrap_components as dbc
import numpy as np
from src.fonctions import (
    get_color_map,
)
from src.glob_vars import COLORS
from src.layout.content_utils.build_graph_data import build_graph_data
from src.layout.content_utils.make_24h_avg import make_24h_avg
from src.layout.content_utils.make_boxplot import make_boxplot
from src.layout.content_utils.make_corr_matrix import make_corr_matrix
from src.layout.content_utils.make_diurnal_cycle import make_diurnal_cycle
from src.layout.content_utils.make_map import make_map
from src.layout.content_utils.make_summary_table import make_summary_table
from src.layout.content_utils.make_timeseries import make_timeseries
from src.layout.styles import CONTENT_STYLE
from maindash import app



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
                                    ),  
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
    quart_data, hour_data = build_graph_data(
        start_date, end_date, site_plus_capteur, polluant, station_name
    )
    graph_data = hour_data if aggregation == "horaire" else quart_data

    color_map = get_color_map(graph_data.columns)

    timeseries_fig = make_timeseries(
        graph_data, color_map, aggregation, polluant, station_name
    )
    week_diurnal_cycle_fig = make_diurnal_cycle(
        graph_data,
        color_map,
        polluant,
        aggregation,
        "Profil journalier en semaine",
        week_section="workweek",
    )
    wend_diurnal_cycle_fig = make_diurnal_cycle(
        graph_data,
        color_map,
        polluant,
        aggregation,
        "Profil journalier en week-end",
        week_section="weekend",
    )
    fig_boxplot = make_boxplot(
        graph_data, color_map, aggregation, polluant, station_name
    )
    fig_corr = make_corr_matrix(graph_data)
    columns, data = make_summary_table(graph_data, hour_data, polluant, station_name)
    fig_24h_avg = make_24h_avg(
        graph_data, color_map, aggregation, polluant, station_name
    )
    fig_map = make_map(
        graph_data,
        color_map,
        polluant,
        start_date,
        end_date,
        station_name,
    )

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
