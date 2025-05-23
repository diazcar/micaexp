from dash import html, dcc, Output, Input, State, ctx
import dash
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
from src.utils.glob_vars import TIME_NOW
from src.layout.styles import SIDEBAR_STYLE
from src.api_calls.microspot_api import request_microspot
from src.api_calls.xair import ISO, request_xr, time_window
from maindash import app


def get_sidebar():
    return html.Div(
        [
            html.Img(src="assets/logo_atmosud_inspirer_web.png"),
            html.Hr(),
            html.B("Polluant"),
            dcc.Dropdown(
                options=["PM10", "PM2.5", "PM1"],
                value="PM10",
                id="polluant_dropdown",
                style={"border": "0", "background": "transparent"},
            ),
            html.Hr(),
            html.B("Dates"),
            dcc.DatePickerRange(
                id="my-date-picker-range",
                initial_visible_month=TIME_NOW,
                start_date=time_window(format="%Y-%m-%d")[0],
                end_date=time_window(format="%Y-%m-%d")[1],
                display_format="YYYY-MM-DD",
                style={"font-size": 6},
            ),
            html.Hr(),
            html.B("Pas de temps"),
            dcc.Dropdown(
                options=["quart-horaire", "horaire"],
                value="horaire",
                id="time_step_dropdown",
                style={"border": "0", "background": "transparent"},
            ),
            html.Hr(),
            html.B("Sites (microcapteur_ID) "),
            dcc.Dropdown(
                id="micro_capteur_sites_dropdown",
                className="dropUp",
                multi=True,
                style={"border": "0", "background": "transparent"},
                value=[],  # ← Set default to empty
            ),
            html.Hr(),
            html.B("Station Atmosud"),
            dcc.Dropdown(
                options=[],  # No default options
                id="station_xair_dropdown",
                value=None,  # No default value
                className="dropUp",
                style={"border": "0", "background": "transparent"},
            ),
            html.Hr(),
            html.B("Group Search Configurations"),
            dcc.Input(
                id="group_name_input",
                type="text",
                placeholder="Enter group name",
                style={"width": "100%"},
            ),
            html.Button(
                "Save Search",
                id="save_search_button",
                n_clicks=0,
                style={"margin-top": "5px"},
            ),
            html.Br(),
            html.Br(),
            dcc.Dropdown(id="saved_searches_dropdown", placeholder="Load saved group"),
            html.Button(
                "Load Search",
                id="load_search_button",
                n_clicks=0,
                style={"margin-top": "5px"},
            ),
            html.Button(
                "Delete Search",
                id="delete_search_button",
                n_clicks=0,
                style={
                    "margin-top": "5px",
                    "background-color": "#e57373",
                    "color": "white",
                },
            ),
            dcc.Store(id="saved_searches_store", storage_type="local"),
        ],
        style=SIDEBAR_STYLE,
    )


@app.callback(
    Output("station_xair_dropdown", "options"),
    Input("polluant_dropdown", "value"),
)
def get_station_dropdown(poll: str) -> list:
    list_options = request_xr(
        folder="measures", physicals=ISO[poll], groups="DIDON"
    ).id_site.unique()
    return list_options


@app.callback(
    Output("micro_capteur_sites_dropdown", "options"),
    Input("polluant_dropdown", "value"),
    Input("my-date-picker-range", "start_date"),
    Input("my-date-picker-range", "end_date"),
)
def get_capteur_site_dropdown(poll: str, start_date: str, end_date: str):
    data = request_microspot(
        observationTypeCodes=[ISO[poll]],
        dateRange=[f"{start_date}T00:00:00+00:00", f"{end_date}T00:00:00+00:00"],
        aggregation="horaire",
    )
    data = data[~data.site_name.isnull()]
    data["site_capteurID"] = data.apply(
        lambda row: f"{row['site_name']} - {row['capteur_id']}", axis=1
    )
    options = [{"label": v, "value": v} for v in data["site_capteurID"].unique()]
    return options


@app.callback(
    Output("saved_searches_store", "data"),
    Input("save_search_button", "n_clicks"),
    Input("delete_search_button", "n_clicks"),
    State("group_name_input", "value"),
    State("micro_capteur_sites_dropdown", "value"),
    State("station_xair_dropdown", "value"),
    State("saved_searches_dropdown", "value"),
    State("saved_searches_store", "data"),
    prevent_initial_call=True,
)
def manage_searches(
    save_clicks,
    delete_clicks,
    group_name,
    capteurs,
    station,
    selected_group,
    store_data,
):
    triggered_id = ctx.triggered_id
    store_data = store_data or {}

    if triggered_id == "save_search_button":
        if not group_name:
            return dash.no_update
        store_data[group_name] = {
            "capteurs": capteurs,
            "station": station,
        }
        return store_data

    if triggered_id == "delete_search_button":
        if not selected_group or selected_group not in store_data:
            return dash.no_update
        store_data = store_data.copy()
        store_data.pop(selected_group)
        return store_data

    return dash.no_update


@app.callback(
    Output("micro_capteur_sites_dropdown", "value"),
    Output("station_xair_dropdown", "value"),
    Input("load_search_button", "n_clicks"),
    State("saved_searches_dropdown", "value"),
    State("saved_searches_store", "data"),
)
def load_search(n_clicks, selected_group, store_data):
    if not selected_group or selected_group not in store_data:
        return dash.no_update, dash.no_update
    config = store_data[selected_group]
    return (
        config["capteurs"],
        config["station"],
    )


@app.callback(
    Output("saved_searches_dropdown", "options"),
    Input("saved_searches_store", "data"),
)
def update_saved_searches_options(store_data):
    if not store_data:
        return []
    return [{"label": k, "value": k} for k in store_data.keys()]
