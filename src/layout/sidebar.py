from dash import html, dcc
from datetime import date
from src.layout.styles import SIDEBAR_STYLE

sidebar = html.Div(
    [
        html.Img(src="assets/logo_atmosud_inspirer_web.png"),
        html.Hr(),
        html.P("Polluant", className="lead"),
        html.Div([
            dcc.Dropdown(
                options=['PM10', 'PM2.5', 'PM1'],
                value='PM1',
                id="polluant_dropdown",
            )
        ]),
        html.Hr(),
        html.P("Dates", className="lead"),
        html.Div([
            dcc.DatePickerRange(
                id='my-date-picker-range',
                min_date_allowed=date(2020, 1, 1),
                max_date_allowed=date(2024, 7, 1),
                initial_visible_month=date(2020, 1, 1),
                end_date=date(2024, 7, 1),
                style={'font-size': 6}
            ),
            html.Div(id='output-container-date-picker-range')
        ]),
        html.Hr(),
        html.P("Pas de temp", className="lead"),
        html.Div([
            dcc.Dropdown(
                options=['Horaire', 'Journalière', 'Mensuelle'],
                value='Horaire',
                id="time_step_dropdown",
            )
        ]),
        html.Hr(),
        html.P("Micro-Capteur", className="lead"),
        html.Div([
            dcc.Dropdown(
                options=['MC1', 'MC2', 'MC3'],
                value='MC1',
                id="micro_capteur_dropdown",
            )
        ]),
        html.Hr(),
        html.P("Station Atmosud", className="lead"),
        html.Div([
            dcc.Dropdown(
                options=[
                    "Station 1",
                    "Station 2",
                    "Station 3",
                ],
                value='Station 1',
                id="station_xair_dropdown",
            )
        ]),
    ],
    style=SIDEBAR_STYLE,
)
