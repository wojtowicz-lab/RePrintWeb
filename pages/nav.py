import dash_mantine_components as dmc
from dash import dcc, html
from dash_iconify import DashIconify

# Custom styles for the navbar
NAVBAR_STYLES = {
    "background": "linear-gradient(135deg, #2563EB 0%, #1e40af 100%)",
    "padding": "1rem 2rem",
    "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.15)",
}

NAVBAR_LINK_STYLES = {
    "color": "white",
    "fontSize": "0.95rem",
    "fontWeight": "600",
    "transition": "all 0.3s ease",
    "padding": "0.625rem 1.25rem",
    "borderRadius": "0.5rem",
    "cursor": "pointer",
    "display": "inline-block",
}

NAVBAR_LINK_HOVER_STYLES = {
    **NAVBAR_LINK_STYLES,
    "backgroundColor": "rgba(255, 255, 255, 0.2)",
}

# Create navbar
navbar = html.Header(
    style={**NAVBAR_STYLES, "height": "70px"},
    children=dmc.Container(
        size="xl",
        style={"display": "flex", "justifyContent": "space-between", "alignItems": "center"},
        children=[
            # Brand/Logo
            html.A(
                href="/",
                style={"display": "flex", "alignItems": "center", "textDecoration": "none", "color": "white"},
                children=[
                    html.Img(
                        src="/assets/logo.png",
                        height="30px",
                        style={"marginRight": "12px"}
                    ),
                    html.Span("RePrint", style={"fontSize": "1.5rem", "fontWeight": "700"}),
                ]
            ),
            # Center Navigation Links
            html.Div(
                style={"display": "flex", "gap": "2rem", "alignItems": "center"},
                children=[
                    html.A(
                        "Start page",
                        href="/",
                        id="nav-home",
                        style=NAVBAR_LINK_STYLES,
                        className="navbar-link"
                    ),
                    html.A(
                        "RePrints charts",
                        href="/page1",
                        id="nav-page1",
                        style=NAVBAR_LINK_STYLES,
                        className="navbar-link"
                    ),
                    html.A(
                        "Merge signatures",
                        href="/page3",
                        id="nav-page4",
                        style=NAVBAR_LINK_STYLES,
                        className="navbar-link"
                    ),
                ]
            ),
        ]
    ),
)