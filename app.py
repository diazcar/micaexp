import argparse
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

from src.fonctions import list_of_strings
from src.layout.sidebar import get_sidebar
from src.layout.content import get_content
from maindash import app

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
parser.add_argument(
    "-rs", "--reference_stations",
    metavar="\b",
    type=list_of_strings,
    help="""
    List of reference stations to compare
    """,
    default=["NCA"]
)
parser.add_argument(
    "-iso", "--poll_iso",
    metavar="\b",
    type=list_of_strings,
    help="""
    List of pollutant iso in {PM10:24, PM2.5:39 ,PM1:68}
    """,
    default="24"
)
parser.add_argument(
    "-o", "--output",
    metavar="\b",
    type=str,
    help=""",
    Output path for csv file
    """,
    default="./",
)
parser.add_argument(
    "-n", "--name",
    metavar="\b",
    type=str,
    help=""",
    Name of the outputfile
    """,
    default="xair_data",
)

args = parser.parse_args()


if __name__ == '__main__':
    app.layout = html.Div(
        [
            dcc.Location(id="url"),
            get_sidebar(),
            get_content(),
            ]
    )
    app.run_server(debug=True)
