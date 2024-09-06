from dash import html, dcc
from src.layout.sidebar import get_sidebar
from src.layout.content import get_content
from maindash import app

app.layout = html.Div(
        [
            dcc.Location(id="url"),
            get_sidebar(),
            get_content(),
            # html.Hr(
            #     style={
            #         'borderWidth': "0.5rem",
            #         "width": "100%",
            #         "color": "#17BECF",
            #         }
            # ),
            ]
    )

server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)
