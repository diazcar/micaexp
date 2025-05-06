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
    get_color_map
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
                                        style=dict(height="30vh"),
                                    )
                                ],
                                width=6,
                            ),
                            dbc.Col(
                                [
                                    dcc.Graph(
                                        figure={},
                                        id="diurnal_cycle_weekend",
                                        style=dict(height="30vh"),
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
                                ],
                                width=7,
                            ),
                            dbc.Col(
                                [
                                    dcc.Graph(figure={}, id="map"),
                                ],
                                width=5,
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
    Input("micro_capteur_sites_dropdown", "value"),
    Input("polluant_dropdown", "value"),
)
def build_title(microcapteur: str, poll: str):
    nom_site = microcapteur.split(" - ")[0]
    return html.B(
        html.Center(f"Données {poll} du microcapteur {nom_site}"),
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
    site_plus_capteur: str,
    polluant: str,
    start_date: str,
    end_date: str,
    station_name: str,
):
    cap_name, cap_id = site_plus_capteur.rsplit(" - ", 1)
    source_select = ["capteur", "station"]
    names = [cap_name, station_name]
    # ---------------------------------------------------
    #                       MAP
    # ---------------------------------------------------
    gdf = get_geoDF(
        id_capteur=int(cap_id),
        polluant=polluant,
        start_date=start_date,
        end_date=end_date,
        nom_station=station_name,
    )

    fig_map = go.Figure(layout=dict(height=600, width=800))

    # zoom, center = get_zoom_level_and_center(
    #     longitudes=gdf['lon'].values,
    #     latitudes=gdf['lat'].values
    # )

    for i in gdf.index:
        fig_map.add_trace(
            go.Scattermapbox(
                lat=[gdf.geometry.y[i]],
                lon=[gdf.geometry.x[i]],
                name=f"{names[i]}",
                mode="markers",
                marker=dict(size=15, color=COLORS["markers"][source_select[i]]),
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
    Output("summary_table", "columns"),
    Output("summary_table", "data"),
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
    site_plus_capteur: str,
    polluant: str,
    station_name: str = None,
    aggregation: str = "quart-horaire",
):
    print(site_plus_capteur.rsplit(" - ", 1))
    cap_name = site_plus_capteur.rsplit(" - ", 1)[0]
    cap_id = int(site_plus_capteur.rsplit(" - ", 1)[1])
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
    #####################################################
    #                 GET DATA                          #
    #####################################################

    capteur_quart_data = request_microspot(
        observationTypeCodes=[ISO[polluant]],
        devices=[cap_id],
        aggregation="quart-horaire",
        dateRange=[f"{start_date}T00:00:00+00:00", f"{end_date}T00:00:00+00:00"],
    )
    capteur_quart_data = capteur_quart_data[capteur_quart_data.isoCode == ISO[polluant]]

    capteur_hour_data = request_microspot(
        observationTypeCodes=[ISO[polluant]],
        devices=[cap_id],
        aggregation="horaire",
        dateRange=[f"{start_date}T00:00:00+00:00", f"{end_date}T00:00:00+00:00"],
    )
    capteur_hour_data = capteur_hour_data[capteur_quart_data.isoCode == ISO[polluant]]

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

    # After fetching your dataframes (capteur_quart_data, station_quart_data, etc.)

    # Rename columns for clarity
    station_col_name = "station"
    micro_col_name = f"microcapteur_{cap_id}"  # or use cap_name if you prefer

    # For hourly data
    capteur_hour_data = capteur_hour_data.rename(
        columns={"valueModified": micro_col_name}
    )
    station_hour_data = station_hour_data.rename(columns={"value": station_col_name})
    hour_data = pd.concat(
        [station_hour_data[station_col_name], capteur_hour_data[micro_col_name]], axis=1
    )

    # For quart-horaire data
    capteur_quart_data = capteur_quart_data.rename(columns={"valueRaw": micro_col_name})
    station_quart_data = station_quart_data.rename(columns={"value": station_col_name})
    quart_data = pd.concat(
        [station_quart_data[station_col_name], capteur_quart_data[micro_col_name]],
        axis=1,
    )

    # Now, graph_data will always have columns: ["station", "microcapteur_<id>"]
    if aggregation == "horaire":
        graph_data = hour_data
    else:
        graph_data = quart_data


    if aggregation == "quart-horaire":
        dcycle_xticks_div = 2
    if aggregation == "horaire":
        dcycle_xticks_div = 1

    # -------------------------------------
    #           DIURNAL CYCLE DATA
    # -------------------------------------

    capteur_value_var = f"microcapteur_{cap_id}"

    week_diurnal_cycle_data = weekday_profile(
        aggregation=aggregation,
        capteur_value_var=capteur_value_var,
        data=graph_data,
        week_section="workweek",
    )
    wend_diurnal_cycle_data = weekday_profile(
        aggregation=aggregation,
        capteur_value_var=capteur_value_var,
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
        # xaxis_title=f"{aggregation}",
        xaxis={"dtick": dtick},
        yaxis_title=f"{polluant} {UNITS[polluant]}",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(
            b=0,
            l=0,
            r=0,
            t=0,
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
        ),
        yaxis_title=f"{polluant} {UNITS[polluant]}",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(
            b=0,
            l=0,
            r=0,
            t=80,
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
        ),
        yaxis_title=f"{polluant} {UNITS[polluant]}",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(
            b=0,
            l=0,
            r=0,
            t=80,
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
            title=f"{polluant} {UNITS[polluant]}",
            # tickvals=ytick_vals,
        ),
        xaxis_title="",
        xaxis2_showticklabels=False,
        showlegend=False,
        margin=dict(
            b=0,
            l=0,
            r=0,
            t=25,
        ),
        yaxis_range=[0, 100],
        # yaxis_range=[0, y_max+y_max*.05]
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

    # Build a summary DataFrame
    summary_df = pd.DataFrame(
        {
            "Microcapteur": [
                f"{cap_name}",
                f"{moyenne_periode[0]:.0f}",
                f"{min_periode[0]:.0f} / {max_periode[0]:.0f}",
                f"{count_seuil_information[0]}",
                f"{count_seuil_alert[0]}",
            ],
            "Station": [
                f"{station_name}",
                f"{moyenne_periode[1]:.0f}",
                f"{min_periode[1]:.0f} / {max_periode[1]:.0f}",
                f"{count_seuil_information[1]}",
                f"{count_seuil_alert[1]}",
            ],
        },
        index=[
            "Nom",
            "Moyenne période (µg/m³)",
            "Min / Max horaire (µg/m³)",
            f"Dépassements seuil info ({seuil_information} µg/m³/24h)",
            f"Dépassements seuil alerte ({seuil_alert} µg/m³/24h)",
        ],
    )

    summary_df_reset = summary_df.reset_index().rename(columns={"index": " "})
    columns = [{"name": col, "id": col} for col in summary_df_reset.columns]
    data = summary_df_reset.to_dict("records")

    return (
        timeseries_fig,
        week_diurnal_cycle_fig,
        wend_diurnal_cycle_fig,
        fig_boxplot,
        columns,
        data,
    )


@app.callback(
    Output("micro_capteur_info", "children"),
    Input("micro_capteur_sites_dropdown", "value"),
)
def get_micro_capteur_info(nom_site: str):
    return None
    # json_data = request_api_observations(
    #     folder_key='sites',
    #     nom_site=nom_site.split(" - ")[0],
    #     format='json',
    #     download='false',
    # )

    # return html.P([
    #     # html.B("id_site: "),
    #     # html.H6(f"{json_data['id_site'].values[0]}"),
    #     html.B("Nom du site: "),
    #     html.H6(f"{json_data['nom_site'].values[0]}"),
    #     # html.B("type_site:"),
    #     # html.H6(f"{json_data['type_site'].values[0]}"),
    #     html.B("Influence: "),
    #     html.H6(f"{json_data['influence'].values[0]}"),
    #     html.B("Longitude: "),
    #     html.H6(f"{json_data['lon'].values[0]: 0.4f}"),
    #     html.B("Latitude: "),
    #     html.H6(f"{json_data['lat'].values[0]: 0.4f}"),
    #     # html.B("date_debut_site: "),
    #     # html.H6(f"{json_data['date_debut_site'].values[0].split('T')[0]}"),
    #     # html.B("date_fin_site: "),
    #     # html.H6(f"{json_data['date_fin_site'].values[0].split('T')[0]}"),
    #     # html.B("ID campagne: "),
    #     # html.H6(f"{json_data['id_campagne'].values[0]}"),
    #     html.B("Nom campagne: "),
    #     html.H6(f"{json_data['nom_campagne'].values[0]}"),
    #     # html.B("ID capteur: "),
    #     # html.H6(f"{json_data['id_capteur'].values[0]}"),
    #     html.B("Marque capteur: "),
    #     html.H6(f"{json_data['marque_capteur'].values[0]}"),
    #     # html.B("Modele capteur : "),
    #     # html.H6(f"{json_data['modele_capteur'].values[0]}"),
    #     html.B("Variables: "),
    #     html.H6("PM10, PM2.5 et PM1"),
    #     ]
    # )


@app.callback(
    Output("station_info", "children"),
    Input("station_xair_dropdown", "value"),
)
def get_station_info(nom_site: str):

    json_data = request_xr(
        folder="sites",
        sites=nom_site,
    )

    return None
    # return html.P([
    #     # html.B("id_site:"),
    #     # html.H6(f"{json_data['id'].values[0]}"),
    #     html.B("Nom site: "),
    #     html.H6(f"{json_data['labelSite'].values[0]}"),
    #     # html.B("type_site: "),
    #     # html.H6("Fixe"),
    #     html.B("Influence: "),
    #     # html.H6(f"{json_data['locationTypeLabel'].values[0]}"),
    #     html.B("Longitude: "),
    #     html.H6(f"{json_data['longitude'].values[0]: 0.4f}"),
    #     html.H6(f"{json_data['latitude'].values[0]: 0.4f}"),
    #     # html.B("date_debut_site: "),
    #     # html.H6(f"{str(json_data['startDate'].values[0]).split('T')[0]}"),
    #     # html.B("date_fin_site: "),
    #     # html.H6(f"{str(json_data['stopDate'].values[0]).split('T')[0]}"),
    #     html.B("Department: "),
    #     html.H6(f"{json_data['labelDepartment'].values[0]}"),
    #     html.B("Commune: "),
    #     html.H6(f"{json_data['labelCommune'].values[0]}"),
    #     html.B("Environment: "),
    #     # html.H6(f"{json_data['classTypeLabel'].values[0]}"),
    #     html.B("Activité de la Zone: "),
    #     # html.H6(f"{json_data['zoneOfActivityLabel'].values[0]}"),
    #     ]
    # )
