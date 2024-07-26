from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
from plotly import graph_objects as go
import numpy as np
from src.fonctions import weekday_profile
from src.layout.styles import CONTENT_STYLE
from maindash import app
from src.routines.micro_capteurs import (
    ISO,
    get_site_info,
    request_api_observations,
)
from src.routines.xair import DATATYPES, request_xr, wrap_xair_request


def get_content():
    return html.Div(
        [
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        figure={},
                        id="timeseries",
                        style={'height': '60vh'}
                        ),
                    ], width=12),
            ]),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure={}, id="diurnal_cycle_workweek")
                    ], width=6),
                dbc.Col([
                    dcc.Graph(figure={}, id="diurnal_cycle_weekend")
                    ], width=6),
                ]),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure={}, id="boxplot"),
                    ], width=6),
                dbc.Col([
                    dcc.Graph(figure={}, id="scatter_plot"),
                    ], width=6),
                ]),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H3('Information Micro Capteur'),
                            html.H4(id='micro_capteur_info'),
                            ]),
                        ],
                    ),
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H3("Information de la station AtmoSud"),
                            html.H4(id='station_info'),
                            ]),
                        ],
                    ),
                ], width=6)
            ]),
            html.Hr(),
            dbc.Row([
                dbc.Card([
                        dbc.CardBody([
                            html.H3("Disclaimer text"),
                            ]),
                        ],
                    ),
            ])
        ],
        style=CONTENT_STYLE,
    )


@app.callback(
        Output('timeseries', 'figure'),
        Output('diurnal_cycle_workweek', 'figure'),
        Output('diurnal_cycle_weekend', 'figure'),
        Output('boxplot', 'figure'),
        Output('scatter_plot', 'figure'),
        Input('my-date-picker-range', 'start_date'),
        Input('my-date-picker-range', 'end_date'),
        Input('micro_capteur_sites_dropdown', 'value'),
        Input('polluant_dropdown', 'value'),
        Input('station_xair_dropdown', 'value'),
        Input('time_step_dropdown', 'value')
)
def build_graphs(
    start_date: np.datetime64,
    end_date: np.datetime64,
    site_plus_capteur: str,
    polluant: str,
    station_name: str = None,
    aggregation: str = 'quart_horaire',
):
    cap_name = site_plus_capteur.split(" - ")[0]

    #####################################################
    #                 GET DATA                          #
    #####################################################
    capteur_data = request_api_observations(
        folder_key='mesures',
        start_date=start_date,
        end_date=end_date,
        id_site=get_site_info(
            col_key="site_plus_capteur",
            search_key=site_plus_capteur,
            col_target='id_site'
        ),
        id_variable=ISO[polluant],
        nb_dec=4,
        aggregation='quart-horaire'
    )

    station_data = wrap_xair_request(
            fromtime=start_date,
            totime=end_date,
            keys='data',
            sites=station_name,
            physicals=ISO[polluant],
            datatype='base'
        )

    if station_data.value.isnull().all():
        station_name = "NO_DATA"

    capteur_data.to_csv("./notebook/timeseries_test.csv")
    station_data.to_csv("./notebook/timeseries_station_test.csv")

    graph_capteur_data = capteur_data[capteur_data.variable == polluant]

    unit = graph_capteur_data.unite.unique()[0]

    graph_data = pd.concat(
        [graph_capteur_data['valeur_ref'], station_data['value']],
        axis=1,
    )
    graph_data.index.name = 'date'
    names = [cap_name, station_name]
    # ---------------------------------------------------
    #  CAPTEUR             TIMESERIES
    # ---------------------------------------------------
    timeseries_fig = go.Figure()

    for i, col in enumerate(graph_data.columns):
        timeseries_fig.add_trace(
            go.Scatter(
                y=graph_data[col],
                x=graph_data.index,
                name=names[i],
            )
        )

    timeseries_fig.update_layout(
            title="".join(
                [
                    f"Micro Capteur : {cap_name}",
                    "| Référence Station : ",
                    f"{station_name}<br>{polluant}",
                ]
            ),
            title_x=0.5,
            xaxis_title="Date",
            yaxis_title=f"{polluant} {unit}",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
                )
    )
    # ---------------------------------------------------
    # CAPTEUR         WEEKDAY DIURNAL CYCLE
    # ---------------------------------------------------
    week_diurnal_cycle_fig = go.Figure()

    # ymin, ymax
    week_diurnal_cycle_data = weekday_profile(
        data=graph_data,
        week_section='workweek',
    )

    for i, col in enumerate(graph_data.columns):
        week_diurnal_cycle_fig.add_trace(
            go.Scatter(
                y=week_diurnal_cycle_data[col],
                x=week_diurnal_cycle_data.index,
                name=names[i],
            )
        )

    week_diurnal_cycle_fig.update_layout(
            title="Profile journalière en semaine",
            title_x=0.5,
            xaxis_title="Date",
            yaxis_title=f"{polluant} {unit}",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
                )
    )

    # ---------------------------------------------------
    #         WENDDAY DIURNAL CYCLE
    # ---------------------------------------------------
    wend_diurnal_cycle_fig = go.Figure()

    wend_diurnal_cycle_data = weekday_profile(
        data=graph_data,
        week_section='weekend',
    )

    for i, col in enumerate(graph_data.columns):
        wend_diurnal_cycle_fig.add_trace(
            go.Scatter(
                y=wend_diurnal_cycle_data[col],
                x=wend_diurnal_cycle_data.index,
                name=names[i],
            )
        )

    wend_diurnal_cycle_fig.update_layout(
            title="Profile journalière en fin de semaine",
            title_x=0.5,
            xaxis_title="Date",
            yaxis_title=f"{polluant} {unit}",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
                )
    )

    # ---------------------------------------------------
    #        BOXPLOT CAPTEUR
    # ---------------------------------------------------
    fig_boxplot = go.Figure()

    for i, col in enumerate(graph_data.columns):
        fig_boxplot.add_trace(
            go.Box(
                y=graph_data[col],
                name=names[i],
            )
        )

    fig_boxplot.update_layout(
        title="Boxplot",
        title_x=0.5,
        yaxis_title=f"{polluant} {unit}",
        xaxis_title='',
        showlegend=False
    )

    # ---------------------------------------------------
    #         SCATTER PLOT
    # ---------------------------------------------------
    fig_scatterplot = go.Figure()

    fig_scatterplot.add_trace(
        go.Scatter(
            x=station_data['value'],
            y=graph_capteur_data['valeur_ref'],
            mode='markers',
            marker_color='purple',
            )
    )

    fig_scatterplot.update_layout(
        title=f"Scatterplot : {cap_name}/{station_name}",
        title_x=0.5,
        xaxis_title=station_name,
        yaxis_title=cap_name,
    )

    return (
        timeseries_fig,
        week_diurnal_cycle_fig,
        wend_diurnal_cycle_fig,
        fig_boxplot,
        fig_scatterplot,
        )


@app.callback(
    Output('micro_capteur_info', 'children'),
    Input('micro_capteur_sites_dropdown', 'value'),
)
def get_micro_capteur_info(nom_site: str):

    json_data = request_api_observations(
        folder_key='sites',
        nom_site=nom_site.split(" - ")[0],
        format='json',
        download='false',
    )

    return html.P([
        f"id_site : {json_data['id_site'].values[0]}", html.Br(),
        f"nom_site: {json_data['nom_site'].values[0]}", html.Br(),
        f"type_site : {json_data['type_site'].values[0]}", html.Br(),
        f"influence : {json_data['influence'].values[0]}", html.Br(),
        f"lon : {json_data['lon'].values[0]}",html.Br(),
        f"lat : {json_data['lat'].values[0]}",html.Br(),
        # f"code_station_commun : {json_data['code_station_commun'].values[0]}", html.Br(),
        f"date_debut_site : {json_data['date_debut_site'].values[0].split('T')[0]}", html.Br(),
        f"date_fin_site : {json_data['date_fin_site'].values[0].split('T')[0]}", html.Br(),
        # "alti_mer : {json_data['alti_mer'].values[0]}",html.Br(),
        # "alti_sol : {json_data['alti_sol'].values[0]}",html.Br(),
        f"id_campagne : {json_data['id_campagne'].values[0]}", html.Br(),
        f"nom_campagne : {json_data['nom_campagne'].values[0]}", html.Br(),
        f"id_capteur : {json_data['id_capteur'].values[0]}", html.Br(),
        f"marque_capteur : {json_data['marque_capteur'].values[0]}", html.Br(),
        f"modele_capteur : {json_data['modele_capteur'].values[0]}", html.Br(),
        "variables : PM10, PM2.5 et PM1", html.Br(),
        ]
    )

@app.callback(
    Output('station_info', 'children'),
    Input('station_xair_dropdown', 'value'),
)
def get_station_info(nom_site: str):

    json_data = request_xr(
        folder='sites',
        sites=nom_site,
    )
    print(json_data.columns)

    return html.P([
        f"id_site : {json_data['id'].values[0]}", html.Br(),
        f"nom_site: {json_data['labelSite'].values[0]}", html.Br(),
        f"type_site : Fix", html.Br(),
        f"influence : {json_data['locationTypeLabel'].values[0]}", html.Br(),
        f"lon : {json_data['longitude'].values[0]}", html.Br(),
        f"lat : {json_data['latitude'].values[0]}", html.Br(),
        f"date_debut_site : {str(json_data['startDate'].values[0]).split('T')[0]}", html.Br(),
        f"date_fin_site : {str(json_data['stopDate'].values[0]).split('T')[0]}", html.Br(),
        f"Department : {json_data['labelDepartment'].values[0]}", html.Br(),
        f"Commune : {json_data['labelCommune'].values[0]}", html.Br(),
        f"Environment : {json_data['classTypeLabel'].values[0]}", html.Br(),
        f"Activité de la Zone : {json_data['zoneOfActivityLabel'].values[0]}", html.Br(),
        ]
    )

