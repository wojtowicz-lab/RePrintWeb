import dash_bootstrap_components as dbc
from dash import dcc, html

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Start page", href="/", id="nav-home")),
        dbc.NavItem(dbc.NavLink("Reprints COSMIC", href="/page1", id="nav-page1")),
        #dbc.NavItem(dbc.NavLink("Custom Reprints", href="/page2", id="nav-page2")),
        dbc.NavItem(dbc.NavLink("Merge signatures", href="/page3", id="nav-page4")),
    ],
    brand=html.Div([
        html.Img(src="/assets/logo.png", height="30px", style={"marginRight": "10px"}),
        "RePrint"
    ], style={"display": "flex", "alignItems": "center"}),
    brand_href="/",
    color="primary",
    dark=True,
)