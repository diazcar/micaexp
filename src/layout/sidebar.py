from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
from src.glob_vars import TIME_NOW
from src.layout.styles import SIDEBAR_STYLE
from src.routines.microspot_api import request_microspot
from src.routines.xair import (
    ISO,
    request_xr,
    time_window,
    )

from maindash import app


def get_sidebar():
    return html.Div(
        [
            html.Img(src="assets/logo_atmosud_inspirer_web.png"),
            html.Hr(),
            html.B("Polluant"),
            html.Div(
                [
                    dcc.Dropdown(
                        options=['PM10', 'PM2.5', 'PM1'],
                        value='PM10',
                        id="polluant_dropdown",
                        style={
                            "border": "0",
                            "background": "transparent"}
                    )
                ]
            ),
            html.Hr(),
            html.B("Dates"),
            html.Div(
                [
                    dcc.DatePickerRange(
                        id='my-date-picker-range',
                        # max_date_allowed=TIME_NOW,
                        # min_date_allowed=TIME_NOW,
                        initial_visible_month=TIME_NOW,
                        start_date=time_window(format="%Y-%m-%d")[0],
                        end_date=time_window(format="%Y-%m-%d")[1],
                        display_format='YYYY-MM-DD',
                        style={
                            'font-size': 6,
                            },
                    ),
                    html.Div(id='output-container-date-picker-range')
                ]
            ),
            html.Hr(),
            html.B("Pas de temps"),
            html.Div(
                [
                    dcc.Dropdown(
                        options=[
                            'quart-horaire',
                            'horaire',
                            ],
                        value='horaire',
                        id="time_step_dropdown",
                        style={
                            "border": "0",
                            "background": "transparent"},
                    )
                ]
            ),
            # html.Hr(),
            # html.P("Campagne", className="lead"),
            # html.Div(
            #     [
            #         dcc.Dropdown(
            #             options=['C1', 'C2', 'C3'],
            #             value=None,
            #             id="campagne_dropdown",
            #         )
            #     ]
            # ),
            html.Hr(),
            html.B("Sites (microcapteur_ID) "),
            html.Div(
                [
                    dcc.Dropdown(
                        id="micro_capteur_sites_dropdown",
                        className='dropUp',
                        style={
                            "border": "0",
                            "background": "transparent"},
                    )
                ]
            ),
            html.Hr(),
            html.B("Station Atmosud"),
            html.Div(
                [
                    dcc.Dropdown(
                        options=['ARSON'],
                        id="station_xair_dropdown",
                        value='ARSON',
                        className='dropUp',
                        style={
                            "border": "0",
                            "background": "transparent"},
                    )
                ]
            ),
            # html.Hr(),
            # html.H4(html.B('Micro Capteur')),
            # html.H6(id='micro_capteur_info'),
            # html.Br(),
            # html.Hr(),
            # html.H4(html.B("Station AtmoSud")),
            # html.H6(id='station_info'),
            # html.Img(src="assets/boxplot_description.png"),
        ],
        style=SIDEBAR_STYLE,
    )


@app.callback(
    Output('station_xair_dropdown', 'options'),
    Input('polluant_dropdown', 'value'),
)
def get_station_dropdown(
    poll: str,
) -> list:

    list_options = request_xr(
        folder='measures',
        physicals=ISO[poll],
        groups='DIDON').id_site.unique()

    return list_options


@app.callback(
    Output('micro_capteur_sites_dropdown', 'options'),
    Output('micro_capteur_sites_dropdown', 'value'),
    Input('polluant_dropdown', 'value'),
    Input('my-date-picker-range', 'start_date'),
    Input('my-date-picker-range', 'end_date')
)
def get_capteur_site_dropdown(
    poll: str,
    start_date: str,
    end_date: str,
) -> list:

    data = request_microspot(
        observationTypeCodes=[ISO[poll]],
        dateRange=[
            f"{start_date}T00:00:00+00:00",
            f"{end_date}T00:00:00+00:00",
        ],
        aggregation='horaire'
    )
    data = data[~data.site_name.isnull()]
    data['site_capteurID'] = data.apply(lambda row: f"{row['site_name']} - {row['capteur_id']}", axis=1)

    return (data['site_capteurID'].unique(), data['site_capteurID'].unique()[0])
