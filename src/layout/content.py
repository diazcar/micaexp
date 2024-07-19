from dash import html, dcc
import dash_bootstrap_components as dbc
from src.layout.styles import CONTENT_STYLE
from maindash import app
from app import args


def get_content():
    return html.Div(
        [
            dbc.Row([
                dbc.Col([
                    dcc.Graph(figure={}, id="timeseries"),
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
                    ], width=12),
            ]),
            html.Hr(),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H3("Information du micro-capteur"),
                            html.H4("text"),
                            html.H4("text"),
                            html.H4("text"),
                            ]),
                        ],
                    ),
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H3("Information de la station AtmoSud"),
                            html.H4("text"),
                            html.H4("text"),
                            html.H4("text"),
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
                        # style={'padding': '1rem'}
                    ),
            ])
        ],
        style=CONTENT_STYLE,
    )

@app.callback(
    Input=
)
