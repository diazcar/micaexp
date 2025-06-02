from dash import html, dcc
from src.layout.sidebar import get_sidebar
from src.layout.content import get_content
from maindash import app

app.layout = html.Div(
    [
        dcc.Location(id="url"),
        get_sidebar(),
        get_content(),
    ]
)

server = app.server

if __name__ == "__main__":

    app.run(debug=True)
