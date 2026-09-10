import dash_mantine_components as dmc
from dash import dcc, html
from dash_iconify import DashIconify

# Use dcc.Link so navigation doesn't cause full page reload
Link = dcc.Link

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
    "textDecoration": "none",
    "opacity": 0.9,
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
            # Brand/Logo (dcc.Link = no full page reload)
            Link(
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
            # Center Navigation Links (dcc.Link = no full page reload)
            html.Div(
                style={"display": "flex", "gap": "1rem", "alignItems": "center"},
                children=[
                    Link(
                        children=dmc.Group(
                            gap=6,
                            align="center",
                            children=[
                                DashIconify(icon="tabler:home-2", width=18, height=18),
                                dmc.Text("Start page", size="sm", fw=600),
                            ],
                        ),
                        href="/",
                        id="nav-home",
                        style=NAVBAR_LINK_STYLES,
                        className="navbar-link"
                    ),
                    Link(
                        children=dmc.Group(
                            gap=6,
                            align="center",
                            children=[
                                DashIconify(icon="tabler:chart-bar", width=18, height=18),
                                dmc.Text("RePrints charts", size="sm", fw=600),
                            ],
                        ),
                        href="/page1",
                        id="nav-page1",
                        style=NAVBAR_LINK_STYLES,
                        className="navbar-link"
                    ),
                    Link(
                        children=dmc.Group(
                            gap=6,
                            align="center",
                            children=[
                                DashIconify(icon="tabler:git-merge", width=18, height=18),
                                dmc.Text("Merge signatures", size="sm", fw=600),
                            ],
                        ),
                        href="/page3",
                        id="nav-page3",
                        style=NAVBAR_LINK_STYLES,
                        className="navbar-link"
                    ),
                    Link(
                        children=dmc.Group(
                            gap=6,
                            align="center",
                            children=[
                                DashIconify(icon="tabler:affiliate", width=18, height=18),
                                dmc.Text("Community Detection", size="sm", fw=600),
                            ],
                        ),
                        href="/community",
                        id="nav-community",
                        style=NAVBAR_LINK_STYLES,
                        className="navbar-link"
                    ),
                    Link(
                        children=dmc.Group(
                            gap=6,
                            align="center",
                            children=[
                                DashIconify(icon="tabler:help-circle", width=18, height=18),
                                dmc.Text("Help", size="sm", fw=600),
                            ],
                        ),
                        href="/help",
                        id="nav-help",
                        style=NAVBAR_LINK_STYLES,
                        className="navbar-link"
                    ),
                ]
            ),
        ]
    ),
)


# ============================================================================
# LICENSE FOOTER
# ============================================================================
# Shown on the landing page: license name + links to the LICENSE file and
# the source repository on GitHub.
REPO_URL = "https://github.com/wojtowicz-lab/RePrintWeb"
LICENSE_URL = f"{REPO_URL}/blob/main/LICENSE"
LICENSE_NAME = "MIT License"

FOOTER_STYLES = {
    "backgroundColor": "#F8FAFC",
    "borderTop": "1px solid #E5E7EB",
    "padding": "1.25rem 2rem",
    "color": "#6B7280",
    "fontSize": "0.875rem",
}

license_footer = html.Footer(
    style=FOOTER_STYLES,
    children=dmc.Container(
        size="xl",
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "flexWrap": "wrap",
            "gap": "0.75rem",
        },
        children=[
            # Left: license
            dmc.Group(
                gap=6,
                align="center",
                children=[
                    DashIconify(icon="tabler:license", width=18, height=18, color="#2563EB"),
                    dmc.Text("Released under the", size="sm", c="#6B7280"),
                    dmc.Anchor(
                        LICENSE_NAME,
                        href=LICENSE_URL,
                        target="_blank",
                        size="sm",
                        fw=600,
                        underline="hover",
                        c="#2563EB",
                    ),
                ],
            ),
            # Right: source repository
            dmc.Anchor(
                dmc.Group(
                    gap=4,
                    align="center",
                    children=[
                        DashIconify(icon="tabler:brand-github", width=16, height=16),
                        dmc.Text("Source on GitHub", size="sm"),
                    ],
                ),
                href=REPO_URL,
                target="_blank",
                underline="hover",
                c="#2563EB",
            ),
        ],
    ),
)
