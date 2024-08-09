from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import datetime as dt
from plotly import graph_objects as go
import numpy as np
from src.fonctions import clean_outlayers, get_max, get_stats, graph_title, weekday_profile
from src.glob_vars import SEUILS, UNITS
from src.layout.styles import CONTENT_STYLE
from maindash import app
from src.routines.micro_capteurs import (
    ISO,
    get_site_info,
    request_api_observations,
)
from src.routines.xair import request_xr, wrap_xair_request


def get_content():
    return html.Div(
        [
            html.H1(id='title_layout'),
            html.Br(),
            dbc.Row([
                dbc.Col([
                    html.H6(
                        id='names_col',
                    )
                ], width=2),
                dbc.Col([
                    html.H6(
                        id='stats_col_1',
                    )
                ], width=2),
                dbc.Col([
                    html.H6(
                        id='stats_col_2',
                    )
                ], width=4),
                dbc.Col([
                    html.H6(
                        id='stats_col_3',
                    )
                ]),
                dbc.Col([
                    html.H6(
                        id='stats_col_4',
                    )
                ], width=4),
            ]),
            html.Br(),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        figure={},
                        id="timeseries",
                        ),
                    ], width=12),
            ]),
            html.Br(),

            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        figure={},
                        id="diurnal_cycle_workweek",
                        style=dict(
                            height='30vh'
                            )
                        )
                    ], width=12),
                ]),
            html.Br(),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        figure={},
                        id="diurnal_cycle_weekend",
                        style=dict(
                            height='30vh'
                            )
                        )
                    ], width=12),
                ]),
            html.Br(),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure={}, id="boxplot"),
                    ], width=7),
                dbc.Col([
                    # dcc.Graph(figure={}, id="scatter_plot"),
                    html.Img(
                       src="assets/boxplot_description.png",
                       ),
                    ], width=5),
                ]),
            html.Hr(),
            dbc.Row([
                   html.Img(
                       src="assets/definitions.png",
                       style={'height': '70%'}
                       ),
                   html.Img(
                       src="assets/valeurs_de_reference.png",
                       style={'height': '70%'}
                       ),
            ], justify="Center"),
        ],
        style=CONTENT_STYLE,
    )


@app.callback(
        Output("title_layout", 'children'),
        Input('micro_capteur_sites_dropdown', 'value'),
        Input('polluant_dropdown', 'value'),

)
def build_title(microcapteur: str, poll: str):
    nom_site = microcapteur.split(" - ")[0]
    return html.B(
        html.Center(
            f"Observations {poll} du microcapteur sur le site de {nom_site}"
            ),
        )


@app.callback(
        Output('timeseries', 'figure'),
        Output('diurnal_cycle_workweek', 'figure'),
        Output('diurnal_cycle_weekend', 'figure'),
        Output('boxplot', 'figure'),
        # Output('scatter_plot', 'figure'),
        Output('names_col', 'children'),
        Output('stats_col_1', 'children'),
        Output('stats_col_2', 'children'),
        Output('stats_col_3', 'children'),
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
    graph_capteur_data = capteur_data[capteur_data.variable == polluant]

    # graph_capteur_data['rolling_mean'] = (
    #     graph_capteur_data['valeur_ref']
    #     .rolling(window=24, min_periods=1)
    #     .mean()
    #     )

    station_data = wrap_xair_request(
            fromtime=start_date,
            totime=end_date,
            keys='data',
            sites=station_name,
            physicals=ISO[polluant],
            datatype='base'
        )
    # ----------------------------------------------------

    if station_data.value.isnull().all():
        station_name = "NO_DATA"

    # Save data to debug
    capteur_data.to_csv("./notebook/timeseries_test.csv")
    station_data.to_csv("./notebook/timeseries_station_test.csv")

    names = [cap_name, station_name]

    # ---------------------------------------
    # Graphs datas
    # ---------------------------------------
    data = pd.concat(
        [graph_capteur_data['valeur_ref'], station_data['value']],
        axis=1,
    )
    data.index.name = 'date'

    quart_data = clean_outlayers(data)
    hour_data = data.resample('H').mean()
    day_data = data.resample('D').mean()

    if aggregation == 'quart-horaire':
        graph_data = quart_data
        dcycle_xticks_div = 2
    if aggregation == 'horaire':
        graph_data = hour_data
        dcycle_xticks_div = 1
    if aggregation == 'journalière':
        graph_data = day_data
        dcycle_xticks_div = 1

    # -------------------------------------
    #           DIURNAL CYCLE DATA
    # -------------------------------------
    week_diurnal_cycle_data = weekday_profile(
        aggregation=aggregation,
        data=graph_data,
        week_section='workweek',
        )
    wend_diurnal_cycle_data = weekday_profile(
        aggregation=aggregation,
        data=graph_data,
        week_section='weekend',
    )
    
    # -------------------------------------
    #  CAPTEUR             TIMESERIES
    # -------------------------------------
    timeseries_fig = go.Figure()
    y_max = graph_data.max().max()
    for i, col in enumerate(graph_data.columns):
        timeseries_fig.add_trace(
            go.Scatter(
                y=graph_data[col],
                x=graph_data.index,
                name=names[i],
            )
        )

    if polluant in ['PM10', 'PM2.5']:
        for i, seuil in enumerate(list(SEUILS[polluant]['FR'].keys())):
            timeseries_fig.add_trace(
                go.Scatter(
                    y=[SEUILS[polluant]['FR'][seuil]]*len(graph_data.index),
                    x=graph_data.index,
                    name=seuil,
                    line=dict(
                        color='black',
                        dash='dash'
                        ),
                    showlegend=False
                )
            )
            timeseries_fig.add_annotation(
                x=graph_data.index[50],
                y=SEUILS[polluant]['FR'][seuil],
                text=seuil
            )

    dtick = graph_data.index[1] - graph_data.index[0]
    timeseries_fig.update_layout(
            title=graph_title('timeseries', aggregation, polluant),
            title_x=0.5,
            # xaxis_title=f"{aggregation}",
            xaxis={'dtick': dtick},
            yaxis_title=f"{polluant} {UNITS[polluant]}",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(
                b=0,
                l=0,
                r=0,
                t=0,
            ),
        yaxis_range=[0, y_max+y_max*.05]

    )
    # ---------------------------------------------------
    # CAPTEUR         WEEKDAY DIURNAL CYCLE
    # ---------------------------------------------------
    y_max = get_max(
        week_diurnal_cycle_data,
        wend_diurnal_cycle_data
    )

    week_diurnal_cycle_fig = go.Figure()
    for i, col in enumerate(week_diurnal_cycle_data.columns):
        week_diurnal_cycle_fig.add_trace(
            go.Scatter(
                y=week_diurnal_cycle_data[col],
                x=week_diurnal_cycle_data.index,
                name=names[i],
            )
        )

    week_diurnal_cycle_fig.update_layout(
            title="Profile journalier en semaine",
            title_x=0.5,
            xaxis=dict(
                nticks=round(len(week_diurnal_cycle_data.index)/dcycle_xticks_div),
                tick0=week_diurnal_cycle_data.index[1],
                tickformat="%H:%M",
                tickangle=90,

            ),
            yaxis_title=f"{polluant} {UNITS[polluant]}",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(
                b=0,
                l=0,
                r=0,
                t=0,
            ),
            yaxis_range=[0, y_max]
    )

    # ---------------------------------------------------
    #         WENDDAY DIURNAL CYCLE
    # ---------------------------------------------------
    wend_diurnal_cycle_fig = go.Figure()

    for i, col in enumerate(wend_diurnal_cycle_data.columns):
        wend_diurnal_cycle_fig.add_trace(
            go.Scatter(
                y=wend_diurnal_cycle_data[col],
                x=wend_diurnal_cycle_data.index,
                name=names[i],
            )
        )

    wend_diurnal_cycle_fig.update_layout(
            title="Profile journalier en weekend",
            title_x=0.5,
            xaxis=dict(
                tick0=week_diurnal_cycle_data.index[1],
                nticks=round(len(week_diurnal_cycle_data.index)/dcycle_xticks_div),
                tickformat="%H:%M",
                tickangle=90,
            ),
            yaxis_title=f"{polluant} {UNITS[polluant]}",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
                ),
            margin=dict(
                b=0,
                l=0,
                r=0,
                t=0,
            ),
            yaxis_range=[0, y_max]
    )

    # ---------------------------------------------------
    #        BOXPLOT CAPTEUR
    # ---------------------------------------------------
    fig_boxplot = go.Figure()
    y_max = graph_data.max().max()
    fig_boxplot.layout.xaxis2 = go.layout.XAxis(
        overlaying='x',
        range=[0, 1],
        showticklabels=False
        )

    for i, col in enumerate(graph_data.columns):
        fig_boxplot.add_trace(
            go.Box(
                y=graph_data[col],
                name=names[i],
                boxpoints='all',
                boxmean='sd'
            )
        )
    if polluant in ['PM10', 'PM2.5']:
        for i, seuil in enumerate(list(SEUILS[polluant]['FR'].keys())):
            seuil_value = SEUILS[polluant]['FR'][seuil]
            fig_boxplot.add_annotation(
                x=0.2,
                y=SEUILS[polluant]['FR'][seuil],
                text=seuil,
                axref='pixel'
            )

            fig_boxplot.add_scatter(
                x=[0, 1],
                y=[seuil_value, seuil_value],
                mode='lines',
                xaxis='x2',
                showlegend=False,
                line=dict(
                    dash='dash',
                    color="firebrick",
                    width=2
                    )
                )

    fig_boxplot.update_layout(
        title=graph_title('boxplot', aggregation, polluant),
        title_x=0.5,
        yaxis_title=f"{polluant} {UNITS[polluant]}",
        xaxis_title='',
        xaxis2_showticklabels=False,
        showlegend=False,
        margin=dict(
                b=0,
                l=0,
                r=0,
                t=25,
            ),
        yaxis_range=[0, y_max+y_max*.05]

    )

    # ---------------------------------------------------
    #         SCATTER PLOT
    # ---------------------------------------------------
    fig_scatterplot = go.Figure()

    fig_scatterplot.add_trace(
        go.Scatter(
            x=quart_data['value'],
            y=quart_data['valeur_ref'],
            mode='markers',
            marker_color='purple',
            )
    )

    fig_scatterplot.update_layout(
        title=f"Scatterplot : {cap_name}/{station_name}",
        title_x=0.5,
        xaxis_title=station_name,
        yaxis_title=cap_name,
        margin=dict(
                b=0,
                l=0,
                r=0,
                t=25,
            )
    )
    # ---------------------------------------------------
    #         SEUILS DE REFERENCE INFO
    # ---------------------------------------------------
    (
        count_seuil_information,
        count_seuil_alert,
        moyenne_periode,
        seuil_information,
        seuil_alert,
    ) = get_stats(
        data=day_data,
        poll=polluant
        )
    names = html.P([
        html.Br(),
        html.Br(),
        html.B([html.B('Microcapteur'), html.H5(f'{cap_name}:')]),
        html.B([html.B('Station Référence.'), html.H5(f'{station_name}:')])
    ])
    p1 = html.P([
        html.Center([
                html.Br(),
                html.B('Moyenne de '),
                html.B('la période :')
                ]),
        html.Br(),
        html.Center(html.H3(f' {moyenne_periode[0]:.2f}')),
        html.Center(html.H3(f' {moyenne_periode[1]:.2f}'))

    ])
    p2 = html.P([
        html.Center([
                html.B('Nombre de dépassements '),
                html.B("du seuil d'information:"),
                html.Br(),
                html.B(f'({seuil_information} µg/m³ en moyenne sur 24h)'),
            ]),
        html.Br(),
        html.Center(html.H3(f'{count_seuil_information[0]}')),
        html.Center(html.H3(f' {count_seuil_information[1]}'))
    ])
    p3 = html.P([
        html.Center(
            [
                html.B('Nombre de dépassements'),
                html.B(" du seuil d'alerte:"),
                html.Br(),
                html.B(f'({seuil_alert} µg/m³ en moyenne sur 24h)')
            ]
        ),
        html.Br(),
        html.Center(html.H3(f'{count_seuil_alert[0]}')),
        html.Center(html.H3(f'{count_seuil_alert[1]}'))
    ])

    return (
        timeseries_fig,
        week_diurnal_cycle_fig,
        wend_diurnal_cycle_fig,
        fig_boxplot,
        # fig_scatterplot,
        names,
        p1,
        p2,
        p3,
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
        # html.B("id_site: "),
        # html.H6(f"{json_data['id_site'].values[0]}"),
        html.B("Nom du site: "),
        html.H6(f"{json_data['nom_site'].values[0]}"),
        # html.B("type_site:"),
        # html.H6(f"{json_data['type_site'].values[0]}"),
        html.B("influence: "),
        html.H6(f"{json_data['influence'].values[0]}"),
        html.B("Longitude: "),
        html.H6(f"{json_data['lon'].values[0]}"),
        html.B("Latitude: "),
        html.H6(f"{json_data['lat'].values[0]}"),
        # html.B("date_debut_site: "),
        # html.H6(f"{json_data['date_debut_site'].values[0].split('T')[0]}"),
        # html.B("date_fin_site: "),
        # html.H6(f"{json_data['date_fin_site'].values[0].split('T')[0]}"),
        # html.B("ID campagne: "),
        # html.H6(f"{json_data['id_campagne'].values[0]}"),
        html.B("Nom campagne: "),
        html.H6(f"{json_data['nom_campagne'].values[0]}"),
        # html.B("ID capteur: "),
        # html.H6(f"{json_data['id_capteur'].values[0]}"),
        html.B("Marque capteur: "),
        html.H6(f"{json_data['marque_capteur'].values[0]}"),
        # html.B("Modele capteur : "),
        # html.H6(f"{json_data['modele_capteur'].values[0]}"),
        html.B("Variables: "),
        html.H6("PM10, PM2.5 et PM1"),
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

    return html.P([
        # html.B("id_site:"),
        # html.H6(f"{json_data['id'].values[0]}"),
        html.B("Nom site: "),
        html.H6(f"{json_data['labelSite'].values[0]}"),
        # html.B("type_site: "),
        # html.H6("Fixe"),
        html.B("Influence: "),
        html.H6(f"{json_data['locationTypeLabel'].values[0]}"),
        html.B("Longitude: "),
        html.H6(f"{json_data['longitude'].values[0]}"),
        html.B("Latitude: "),
        html.H6(f"{json_data['latitude'].values[0]}"),
        # html.B("date_debut_site: "),
        # html.H6(f"{str(json_data['startDate'].values[0]).split('T')[0]}"),
        # html.B("date_fin_site: "),
        # html.H6(f"{str(json_data['stopDate'].values[0]).split('T')[0]}"),
        html.B("Department: "),
        html.H6(f"{json_data['labelDepartment'].values[0]}"),
        html.B("Commune: "),
        html.H6(f"{json_data['labelCommune'].values[0]}"),
        html.B("Environment: "),
        html.H6(f"{json_data['classTypeLabel'].values[0]}"),
        html.B("Activité de la Zone: "),
        html.H6(f"{json_data['zoneOfActivityLabel'].values[0]}"),
        ]
    )
