from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
from src.glob_vars import TIME_NOW
from src.layout.styles import SIDEBAR_STYLE
from src.routines.xair import (
    ISO,
    request_xr,
    time_window,
    )

from src.routines.micro_capteurs import (
    CAPTEUR_SITE_INFO,
    )

from maindash import app

CAPTEUR_SITE_LIST = CAPTEUR_SITE_INFO.site_plus_capteur.to_list()


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
                        max_date_allowed=TIME_NOW,
                        min_date_allowed=TIME_NOW,
                        initial_visible_month=TIME_NOW,
                        start_date=time_window()[0],
                        end_date=time_window()[1],
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
                            'journalière',
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
            html.B("Sites (MicroCapteurs ID) "),
            html.Div(
                [
                    dcc.Dropdown(
                        options=CAPTEUR_SITE_LIST,
                        value=CAPTEUR_SITE_LIST[0],
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
            html.Hr(),
            html.H4(html.B('Micro Capteur')),
            html.H6(id='micro_capteur_info'),
            html.Br(),
            html.Hr(),
            html.H4(html.B("Station AtmoSud")),
            html.H6(id='station_info'),
        ],
        style=SIDEBAR_STYLE,
    )


@app.callback(
    [
        Output('my-date-picker-range', 'start_date'),
        Output('my-date-picker-range', 'initial_visible_month'),
        Output('my-date-picker-range', 'min_date_allowed'),
        Output('my-date-picker-range', 'max_date_allowed'),
        Output('my-date-picker-range', 'end_date'),
        Input('micro_capteur_sites_dropdown', 'value'),

        ]
)
def site_date_window(site_name):
    date_format = '%Y-%m-%dT%H:%M:%S'

    str_start_date = CAPTEUR_SITE_INFO[
        CAPTEUR_SITE_INFO['site_plus_capteur'] == site_name
        ].date_debut_site.values[0]
    str_end_date = CAPTEUR_SITE_INFO[
        CAPTEUR_SITE_INFO['site_plus_capteur'] == site_name
        ].date_fin_site.values[0]

    min_date = datetime.strptime(str_start_date.split(".")[0], date_format)
    end_date = datetime.strptime(str_end_date.split(".")[0], date_format)

    if end_date > TIME_NOW:
        end_date = TIME_NOW

    start_date = end_date - timedelta(days=30)
    return (
        start_date,
        start_date,
        min_date,
        end_date,
        end_date
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
