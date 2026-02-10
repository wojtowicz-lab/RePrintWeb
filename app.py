from dash import dcc, html
from dash.dependencies import Input, Output
from flask import request
from main import *
from pages.page1 import page1_layout
from pages.page2 import page2_layout
from pages.page4 import page4_layout

server = app.server

_DASH_ROOT_PROXY_PARAM = "__dash"
_DASH_ROOT_PROXY_TARGETS = {
    "layout": ("/_dash-layout", {"GET"}),
    "dependencies": ("/_dash-dependencies", {"GET"}),
    "update-component": ("/_dash-update-component", {"POST"}),
}


@server.before_request
def proxy_dash_endpoints_via_root():
    """
    Work around restrictive reverse-proxy configs that pass only "/".
    We tunnel Dash API calls via "/?__dash=...".
    """
    if request.path != "/":
        return None

    target_key = request.args.get(_DASH_ROOT_PROXY_PARAM)
    if not target_key:
        return None

    target = _DASH_ROOT_PROXY_TARGETS.get(target_key)
    if not target:
        return ("Unknown Dash proxy target", 404)

    endpoint_name, allowed_methods = target
    if request.method not in allowed_methods:
        return ("Method not allowed", 405)

    view = server.view_functions.get(endpoint_name)
    if not view:
        return ("Dash endpoint not found", 404)

    return view()


app.layout = dmc.MantineProvider([
    html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div(id='page-content'),
    ])
])
# Favicon i title
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>DNA Repair Footprint Uncovers Contribution of DNA Repair Mechanism to Mutational Signatures</title>
        {%css%}
        <style>
            .custom-option {
                background-color: #f0f9ff;
                color: #0056b3;
            }
            .custom-option:hover {
                background-color: #cde0f7;
            }
            .dendrogram-container {
                overflow: hidden;
                max-width: 100%;
            }
            .dendrogram-container .js-plotly-plot {
                max-width: 100%;
                overflow: hidden;
            }
            .card {
                overflow: hidden;
            }
            .card-body {
                overflow: hidden;
            }
            .dash-graph {
                max-width: 100%;
                overflow: hidden;
            }
        </style>
        <link rel="icon" href="data:,">
        <script>
            (function () {
                const dashPathToProxyKey = {
                    "/_dash-layout": "layout",
                    "/_dash-dependencies": "dependencies",
                    "/_dash-update-component": "update-component"
                };

                function rewriteDashUrl(rawUrl) {
                    try {
                        const parsed = new URL(rawUrl, window.location.origin);
                        const proxyKey = dashPathToProxyKey[parsed.pathname];
                        if (!proxyKey) {
                            return rawUrl;
                        }
                        parsed.pathname = "/";
                        parsed.searchParams.set("__dash", proxyKey);
                        return parsed.toString();
                    } catch (e) {
                        return rawUrl;
                    }
                }

                const originalFetch = window.fetch;
                if (typeof originalFetch === "function") {
                    window.fetch = function (input, init) {
                        if (typeof input === "string") {
                            return originalFetch(rewriteDashUrl(input), init);
                        }
                        if (input && typeof input.url === "string") {
                            const rewritten = rewriteDashUrl(input.url);
                            if (rewritten !== input.url) {
                                input = new Request(rewritten, input);
                            }
                        }
                        return originalFetch(input, init);
                    };
                }
            })();
        </script>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/':
        return page1_layout
    elif pathname == '/page1':
        return page2_layout
    elif pathname == '/page3':
        return page4_layout

# Callback to set the active state
@app.callback(
    [Output("nav-home", "active"),
     Output("nav-page1", "active"),
     Output("nav-page4", "active")
    ],
    [Input("url", "pathname")]
)
def set_active_nav(pathname):
    # Check the current pathname and return True for the matching NavLink
    if pathname == "/":
        return True, False, False
    elif pathname == "/page1":
        return False, True, False
    elif pathname == "/page3":
        return False, False, True

    return False, False, False


if __name__ == '__main__':
    app.run(debug=True, port=8080)
