from dotenv import load_dotenv
from dash import html, dcc, Input, Output, dash_table, ctx, no_update
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
from src.utils.fonctions import get_color_map
from src.utils.glob_vars import COLORS
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
                        columns=[],
                        data=[],
                        style_table={"overflowX": "auto"},
                        style_cell={"textAlign": "center"},
                    ),
                    html.Br(),
                    dcc.Tabs(
                        [
                            dcc.Tab(
                                label="Séries temporelles",
                                children=[
                                    html.Div(
                                        [
                                            dcc.Graph(id="timeseries"),
                                        ],
                                        style={"padding": "20px"},
                                    )
                                ],
                            ),
                            dcc.Tab(
                                label="Profils journaliers",
                                children=[
                                    html.Div(
                                        [
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        dcc.Graph(
                                                            id="diurnal_cycle_workweek"
                                                        ),
                                                        width=6,
                                                    ),
                                                    dbc.Col(
                                                        dcc.Graph(
                                                            id="diurnal_cycle_weekend"
                                                        ),
                                                        width=6,
                                                    ),
                                                ]
                                            )
                                        ],
                                        style={"padding": "20px"},
                                    )
                                ],
                            ),
                            dcc.Tab(
                                label="Boxplot",
                                children=[
                                    html.Div(
                                        [
                                            dcc.Graph(id="boxplot"),
                                        ],
                                        style={"padding": "20px"},
                                    )
                                ],
                            ),
                            dcc.Tab(
                                label="Moyenne glissante 24h",
                                children=[
                                    html.Div(
                                        [
                                            dcc.Graph(id="avg24h"),
                                        ],
                                        style={"padding": "20px"},
                                    )
                                ],
                            ),
                            dcc.Tab(
                                label="Corrélation",
                                children=[
                                    html.Div(
                                        [
                                            dcc.Graph(id="correlation_matrix"),
                                        ],
                                        style={"padding": "20px"},
                                    )
                                ],
                            ),
                            dcc.Tab(
                                label="Carte",
                                children=[
                                    html.Div(
                                        [
                                            dcc.Graph(id="map"),
                                        ],
                                        style={"padding": "20px"},
                                    )
                                ],
                            ),
                        ]
                    ),
                    html.Br(),
                    html.Button(
                        "Télécharger les données", id="download_btn", n_clicks=0
                    ),
                    dcc.Download(id="download_data"),
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
                            "- Niveau réglementaire de concentration à ne pas dépasser",
                            html.Br(),
                            html.B("Objectif qualité (OQ) "),
                            "- Niveau de concentration à attendre à long terme",
                            html.Br(),
                        ]
                    ),
                ],
            ),
        ],
        style=CONTENT_STYLE,
    )


@app.callback(
    Output("title_layout", "children"),
    Input("polluant_dropdown", "value"),
)
def build_title(poll: str):
    return html.B(html.Center(f"Données {poll}"))


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
    Input("show_thresholds_checkbox", "value"),
)
def build_graphs(
    start_date: np.datetime64,
    end_date: np.datetime64,
    site_plus_capteur: list,
    polluant: str,
    station_name: str = None,
    aggregation: str = "quart-horaire",
    show_thresholds: bool = False,
):
    quart_data, hour_data,gdf = build_graph_data(
        start_date, end_date, site_plus_capteur, polluant, station_name
    )
    graph_data = hour_data if aggregation == "horaire" else quart_data
    color_map = get_color_map(graph_data.columns)

    timeseries_fig = make_timeseries(
        graph_data, color_map, aggregation, polluant, station_name, show_thresholds
    )
    week_diurnal_cycle_fig = make_diurnal_cycle(
        graph_data,
        color_map,
        polluant,
        aggregation,
        "Profil journalier en semaine",
        week_section="workweek",
        station_name=station_name,
        show_thresholds=show_thresholds,
    )
    wend_diurnal_cycle_fig = make_diurnal_cycle(
        graph_data,
        color_map,
        polluant,
        aggregation,
        "Profil journalier en week-end",
        week_section="weekend",
        station_name=station_name,
        show_thresholds=show_thresholds,
    )
    fig_boxplot = make_boxplot(
        graph_data, color_map, aggregation, polluant, station_name, show_thresholds
    )
    fig_corr = make_corr_matrix(graph_data, station_name)
    columns, data = make_summary_table(graph_data, station_name)
    fig_24h_avg = make_24h_avg(
        graph_data, color_map, aggregation, polluant, station_name, show_thresholds
    )
    fig_map = make_map(
        graph_data, color_map, polluant, start_date, end_date, station_name
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


@app.callback(
    Output("download_data", "data"),
    Input("download_btn", "n_clicks"),
    Input("my-date-picker-range", "start_date"),
    Input("my-date-picker-range", "end_date"),
    Input("micro_capteur_sites_dropdown", "value"),
    Input("polluant_dropdown", "value"),
    Input("station_xair_dropdown", "value"),
    Input("time_step_dropdown", "value"),
    prevent_initial_call=True,
)
def download_data(
    n_clicks,
    start_date,
    end_date,
    site_plus_capteur,
    polluant,
    station_name,
    aggregation,
):
    if ctx.triggered_id != "download_btn":
        return no_update
    quart_data, hour_data,gdf = build_graph_data(
        start_date, end_date, site_plus_capteur, polluant, station_name
    )
    graph_data = hour_data if aggregation == "horaire" else quart_data
    # Convert to CSV
    csv_string = graph_data.to_csv(index=True, sep=";")
    return dict(content=csv_string, filename="donnees.csv")
    