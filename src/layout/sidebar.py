from dash import html, dcc, Output, Input
from datetime import date
from src.glob_vars import TIME_NOW
from src.layout.styles import SIDEBAR_STYLE
from src.routines.xair import request_xr, time_window
from maindash import app


def get_sidebar():
    # capteur_list = 
    station_list = request_xr(folder='sites',).id.to_list()
    return html.Div(
        [
            html.Img(src="assets/logo_atmosud_inspirer_web.png"),
            html.Hr(),
            html.P("Polluant", className="lead"),
            html.Div(
                [
                    dcc.Dropdown(
                        options=['PM10', 'PM2.5', 'PM1'],
                        value='PM1',
                        id="polluant_dropdown",
                    )
                ]
            ),
            html.Hr(),
            html.P("Dates", className="lead"),
            html.Div(
                [
                    dcc.DatePickerRange(
                        id='my-date-picker-range',
                        min_date_allowed=date(2020, 1, 1),
                        max_date_allowed=TIME_NOW,
                        initial_visible_month=TIME_NOW,
                        start_date=time_window()[0],
                        end_date=time_window()[1],
                        style={'font-size': 6}
                    ),
                    html.Div(id='output-container-date-picker-range')
                ]
            ),
            html.Hr(),
            html.P("Pas de temp", className="lead"),
            html.Div(
                [
                    dcc.Dropdown(
                        options=['Horaire', 'Journalière', 'Mensuelle'],
                        value='Horaire',
                        id="time_step_dropdown",
                    )
                ]
            ),
            html.Hr(),
            html.P("Campagne", className="lead"),
            html.Div(
                [
                    dcc.Dropdown(
                        options=['C1', 'C2', 'C3'],
                        value=None,
                        id="campagne_dropdown",
                    )
                ]
            ),
            html.Hr(),
            html.P("Micro-Capteur", className="lead"),
            html.Div(
                [
                    dcc.Dropdown(
                        options=['MC1', 'MC2', 'MC3'],
                        value='MC1',
                        id="micro_capteur_dropdown",
                    )
                ]
            ),
            html.Hr(),
            html.P("Station Atmosud", className="lead"),
            html.Div(
                [
                    dcc.Dropdown(
                        options=station_list,
                        value='NCA',
                        id="station_xair_dropdown",
                    )
                ]
            ),
        ],
        style=SIDEBAR_STYLE,
    )
