import sys
import matplotlib
import numpy as np
import pandas as pd
from dash import Dash, html, dcc, Output, Input
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import argparse

from src.routines.xair import (
    add_poll_info,
    get_figure_title,
    get_moymax_data,
    mask_aorp,
    request_xr,
    test_path,
    time_window,
    )

from src.fonctions import (
    list_of_strings,
)

parser = argparse.ArgumentParser(
    prog="micaexp.py",
    description="""
    This is a python plotly-dash application to explore and
    compare microcaptor and reference stations
    """,
    epilog="Author :  Carlos DIAZ, Atmosud."
)
parser.add_argument(
    "-sd", "--start_date",
    metavar="\b",
    type=str,
    help="""
    Start date  in YYYY-MM-DDThh:mm:ss format
    """
)
parser.add_argument(
    "-ed", "--end_date",
    metavar="\b",
    type=str,
    help="""
    End date in YYYY-MM-DDThh:mm:ss format
"""
)
parser.add_argument(
    "-mc", "--micro_capteur_id",
    metavar="\b",
    type=list_of_strings,
    help="""
    List of micro capteurs id's to retrive
"""
)
