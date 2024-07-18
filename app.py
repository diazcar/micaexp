from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

from src.layout.sidebar import sidebar
from src.layout.content import content

app = Dash(__name__,
           suppress_callback_exceptions=True,
           external_stylesheets=[dbc.themes.COSMO],
           meta_tags=[{'name': 'viewport',
                       'content': 'width=device-width, initial-scale=1.0'
                       }
                      ]
           )

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

if __name__ == '__main__':
    app.run_server(debug=True)
