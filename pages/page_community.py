from utils.community import (detect_communities, create_community_graph_figure, empty_community_fig,
                             DEFAULT_K)
from utils.utils import (FILES, DEFAULT_SIGNATURES, reprint, calculate_rmse, calculate_cosine,
                          calculate_js_divergence, parse_signatures, merge_uploaded_signatures,
                          load_example_merged_signatures, EXAMPLE_SIGNATURE_SETS)
from main import app
from dash import dcc, html, Input, Output, State
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from pages.nav import navbar
import pandas as pd
import dash


data = {}
for file in FILES:
    data[file] = pd.read_csv(f'data/signatures/{file}', sep='\t').columns[1:].to_list()

dropdown_options = [{'label': file, 'value': file} for file in FILES]

# The page opens on this bundled example rather than on a bare reference
# file: it is small enough to read at a glance and its DNA-repair knockouts
# give the communities an obvious meaning (see EXAMPLE_SIGNATURE_SETS).
DEFAULT_EXAMPLE_SET = 'cosmic_v2_zou'
_example_df, _example_files = load_example_merged_signatures(example_set=DEFAULT_EXAMPLE_SET)
DEFAULT_EXAMPLE_SIGNATURES = [c for c in _example_df.columns if c != 'Type']
DEFAULT_EXAMPLE_STORE = {
    'signatures_data': _example_df.to_dict('records'),
    'filename': _example_files,
    'info': f"Loaded example dataset ({EXAMPLE_SIGNATURE_SETS[DEFAULT_EXAMPLE_SET]['label']}): {', '.join(_example_files)}",
}

DISTANCE_FUNCTIONS = {'rmse': calculate_rmse, 'cosine': calculate_cosine, 'js_divergence': calculate_js_divergence}

# ============================================================================
# STYLING CONFIGURATION
# ============================================================================
COLORS = {
    "primary_blue": "#2563EB",
    "primary_dark": "#1e40af",
    "bg_light": "#F8FAFC",
    "bg_lighter": "#F0F5FB",
    "white": "#FFFFFF",
    "navy": "#1E293B",
    "teal": "#14B8A6",
    "red": "#E11D48",
    "text_primary": "#1F2937",
    "text_secondary": "#6B7280",
    "border": "#E5E7EB",
    "shadow": "0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04)",
    "shadow_md": "0 4px 12px rgba(0, 0, 0, 0.12), 0 2px 6px rgba(0, 0, 0, 0.06)",
}

# ============================================================================
# APPLICATION LAYOUT
# ============================================================================
page_community_layout = html.Div([
    navbar,

    dmc.Container(
        size="xl",
        style={"backgroundColor": COLORS["bg_light"], "minHeight": "100vh", "paddingTop": "3rem", "paddingBottom": "3rem"},
        children=[
            # Instructions
            dmc.Card(
                style={
                    "backgroundColor": COLORS["white"],
                    "border": f"1px solid {COLORS['border']}",
                    "boxShadow": COLORS["shadow"],
                    "marginBottom": "2.5rem",
                    "borderRadius": "0.75rem",
                },
                children=[
                    dmc.Accordion(
                        children=[
                            dmc.AccordionItem(
                                value="instructions",
                                children=[
                                    dmc.AccordionControl(
                                        html.Div(
                                            style={"display": "flex", "alignItems": "center", "gap": "0.75rem"},
                                            children=[
                                                DashIconify(icon="tabler:affiliate", width=20, height=20, color=COLORS["primary_blue"]),
                                                html.H5("How Community Detection Works", style={"margin": 0, "fontWeight": "600"}),
                                            ]
                                        ),
                                    ),
                                    dmc.AccordionPanel(
                                        children=dmc.Grid(
                                            children=[
                                                dmc.GridCol(
                                                    span=6,
                                                    children=[
                                                        html.H6("1. What this does", style={"fontWeight": "600", "marginBottom": "1rem"}),
                                                        html.P(
                                                            "Instead of cutting a dendrogram (as on the RePrints charts page), this page builds a "
                                                            "mutual k-nearest-neighbour similarity graph over your signatures and runs the Louvain "
                                                            "algorithm to find groups of signatures that are more similar to each other than to the "
                                                            "rest — \"communities\" — by maximizing modularity.",
                                                            style={"fontSize": "0.95rem", "color": COLORS["text_primary"]}
                                                        ),
                                                        html.P(
                                                            "Each signature keeps an edge to its k most similar neighbours, and the edge survives only "
                                                            "if both signatures picked each other. That criterion is local, so a tightly-packed family "
                                                            "and a looser one can both stay visible at the same k — unlike a single global similarity "
                                                            "cutoff, which resolves one only by dissolving the other.",
                                                            style={"fontSize": "0.95rem", "color": COLORS["text_primary"]}
                                                        ),
                                                        html.P(
                                                            "The number of communities is not chosen by hand: it falls out of the optimization, "
                                                            "though Resolution below lets you nudge it toward fewer/larger or more/smaller groups.",
                                                            style={"fontSize": "0.95rem", "color": COLORS["text_primary"]}
                                                        ),
                                                    ]
                                                ),
                                                dmc.GridCol(
                                                    span=6,
                                                    children=[
                                                        html.H6("2. Parameters", style={"fontWeight": "600", "marginBottom": "1rem"}),
                                                        html.Ul([
                                                            html.Li([html.Strong("Resolution: "), "higher values favor more, smaller communities; lower values favor fewer, larger ones."], style={"marginBottom": "0.5rem", "fontSize": "0.9rem"}),
                                                            html.Li([html.Strong("Neighbours (k): "), "how many nearest neighbours each signature keeps. Low k gives a sparse graph where distinct families stay apart; raising k merges them."], style={"marginBottom": "0.5rem", "fontSize": "0.9rem"}),
                                                            html.Li([html.Strong("Mutual neighbours only: "), "keeps an edge only when both signatures rank each other in their top k. Off, one signature can drag an unrelated neighbour into its community."], style={"marginBottom": "0.5rem", "fontSize": "0.9rem"}),
                                                            html.Li([html.Strong("Random Seed: "), "Louvain's greedy optimization and the graph layout are randomized; fixing the seed makes runs reproducible."], style={"fontSize": "0.9rem"}),
                                                        ], style={"paddingLeft": "1.5rem"}),
                                                    ]
                                                ),
                                            ],
                                            grow=True,
                                        )
                                    ),
                                ],
                            ),
                        ]
                    ),
                ]
            ),

            # File Selection
            dmc.Card(
                style={
                    "backgroundColor": COLORS["white"],
                    "border": f"1px solid {COLORS['border']}",
                    "boxShadow": COLORS["shadow"],
                    "marginBottom": "2.5rem",
                    "padding": "2rem",
                    "borderRadius": "0.75rem",
                },
                children=[
                    dmc.Paper(
                        children=[
                            dmc.Group(
                                children=[
                                    DashIconify(icon="tabler:database", width=24, height=24, color=COLORS["primary_blue"]),
                                    dmc.Stack(
                                        children=[
                                            dmc.Text("Active Reference File", size="xs", c="dimmed"),
                                            html.Div(
                                                style={"display": "flex", "alignItems": "center", "gap": "0.5rem"},
                                                children=[
                                                    dmc.Text(id="active-file-display-community", size="md", fw=700, style={"color": COLORS["text_primary"]}),
                                                    dmc.Badge(id="signature-count-community", size="sm", color="blue", variant="light"),
                                                ]
                                            ),
                                        ],
                                        gap=0,
                                    ),
                                ],
                                justify="space-between",
                                grow=True,
                                gap="md",
                            ),
                        ],
                        p="md",
                        radius="md",
                        style={"backgroundColor": "#F0F5FB", "border": f"1px solid {COLORS['border']}"},
                    ),

                    html.Div(style={"marginTop": "1.5rem"}),

                    dmc.Stack(
                        children=[
                            dmc.Text("Change Reference File", size="sm", fw=600),
                            dcc.Dropdown(
                                id='dropdown-community',
                                options=dropdown_options,
                                value=DEFAULT_SIGNATURES,
                            ),
                        ],
                        gap="xs",
                    ),

                    html.Div(style={"marginTop": "2rem"}),

                    dmc.Stack(
                        children=[
                            dmc.Text("Select Signatures", size="sm", fw=600),
                            dcc.Dropdown(
                                id='signatures-dropdown-community',
                                options=[{'label': k, 'value': k} for k in DEFAULT_EXAMPLE_SIGNATURES],
                                multi=True,
                                value=list(DEFAULT_EXAMPLE_SIGNATURES),
                                placeholder="Choose signatures...",
                                style={"minWidth": "200px"},
                            ),
                        ],
                        gap="xs",
                    ),
                ]
            ),

            # Upload
            dmc.Card(
                style={
                    "backgroundColor": COLORS["white"],
                    "border": f"2px dashed {COLORS['primary_blue']}",
                    "borderRadius": "0.75rem",
                    "marginBottom": "2.5rem",
                    "padding": "3rem 2rem",
                    "textAlign": "center",
                    "cursor": "pointer",
                    "background": f"linear-gradient(135deg, {COLORS['white']} 0%, {COLORS['bg_lighter']} 100%)",
                },
                children=[
                    dcc.Upload(
                        id='upload-data-community',
                        children=html.Div([
                            DashIconify(icon="tabler:cloud-upload", width=40, height=40, color=COLORS["primary_blue"], style={"marginBottom": "0.75rem"}),
                            html.P("Drag and drop your signature file(s) here, or click to select", style={"fontSize": "1rem", "fontWeight": "500"}),
                            html.P("Accepted formats: .txt/.tsv (tab-separated) or .csv. Select multiple files to merge them.", style={"fontSize": "0.85rem", "color": COLORS["text_secondary"]})
                        ]),
                        multiple=True,
                        style={"width": "100%", "cursor": "pointer"}
                    ),
                    html.Div(style={"marginTop": "1.25rem"}),
                    dmc.Divider(label="or", labelPosition="center"),
                    html.Div(style={"marginTop": "1.25rem"}),
                    dmc.Button(
                        f"Load Example ({EXAMPLE_SIGNATURE_SETS[DEFAULT_EXAMPLE_SET]['label']})",
                        id="load-example-btn-community",
                        variant="outline",
                        color="teal",
                        size="md",
                        leftSection=DashIconify(icon="tabler:dna-2", width=18),
                    ),
                    dmc.Text(
                        f"{EXAMPLE_SIGNATURE_SETS[DEFAULT_EXAMPLE_SET]['blurb']} "
                        "This example is loaded by default; click to reload it after uploading your own files.",
                        size="xs",
                        c="dimmed",
                        style={"marginTop": "0.5rem"}
                    ),
                    dmc.Button(
                        "Clear Uploaded Signatures",
                        id="clear-upload-btn-community",
                        variant="subtle",
                        color="gray",
                        size="sm",
                        leftSection=DashIconify(icon="tabler:x", width=16),
                        style={"marginTop": "1rem", "display": "none"},
                    ),
                    dmc.Text(
                        "Switches back to the bundled reference file dropdown.",
                        size="xs",
                        c="dimmed",
                        id="clear-upload-hint-community",
                        style={"marginTop": "0.25rem", "display": "none"},
                    ),
                ]
            ),

            html.Div(id='upload-error-message-community'),
            html.Div(id='info_uploader-community'),
            dcc.Store(id='session-community-signatures', storage_type='session', data=DEFAULT_EXAMPLE_STORE),
            dcc.Interval(id='initial-load-community', interval=1000, n_intervals=0, max_intervals=1),
            dcc.Store(id='auto-reload-armed-community', data=False),
            dcc.Store(id='reload-signal-community', data=0),

            # Toolbar
            dmc.Card(
                style={
                    "backgroundColor": COLORS["white"],
                    "border": f"1px solid {COLORS['border']}",
                    "boxShadow": COLORS["shadow"],
                    "marginBottom": "2.5rem",
                    "padding": "2rem",
                    "borderRadius": "0.75rem",
                },
                children=[
                    dmc.Group(
                        justify="center",
                        gap="md",
                        style={"display": "flex", "flexWrap": "wrap"},
                        children=[
                            dmc.Button(
                                "Advanced Options",
                                id="toggle-button-community",
                                color="dark",
                                size="md",
                                style={"backgroundColor": COLORS["navy"]},
                                leftSection=DashIconify(icon="tabler:adjustments", width=18),
                            ),
                            dmc.Button(
                                "Download Community Assignments",
                                id="btn_csv-community",
                                color="teal",
                                size="md",
                                style={"backgroundColor": COLORS["teal"]},
                                leftSection=DashIconify(icon="tabler:download", width=18),
                            ),
                            dmc.Button(
                                "Detect Communities",
                                id="submit-button-community",
                                color="red",
                                size="md",
                                style={"backgroundColor": COLORS["red"]},
                                leftSection=DashIconify(icon="tabler:affiliate", width=18),
                            ),
                        ]
                    ),
                ]
            ),

            # Advanced Options
            dmc.Collapse(
                opened=False,
                id="collapse-form-community",
                children=[
                    dmc.Card(
                        style={
                            "backgroundColor": COLORS["white"],
                            "border": f"1px solid {COLORS['border']}",
                            "boxShadow": COLORS["shadow"],
                            "marginBottom": "2.5rem",
                            "padding": "2rem",
                            "borderRadius": "0.75rem",
                        },
                        children=[
                            dmc.Grid(
                                children=[
                                    dmc.GridCol(
                                        span=6,
                                        children=[
                                            dmc.Text("Distance Metric", size="sm", fw=600, style={"marginBottom": "0.5rem"}),
                                            dcc.Dropdown(
                                                id='distance-metric-community',
                                                options=[
                                                    {'label': 'Cosine', 'value': 'cosine'},
                                                    {'label': 'RMSE', 'value': 'rmse'},
                                                    {'label': 'JS Divergence', 'value': 'js_divergence'}
                                                ],
                                                value='rmse',
                                                clearable=False,
                                                style={"width": "100%"}
                                            ),
                                        ]
                                    ),
                                    dmc.GridCol(
                                        span=6,
                                        children=[
                                            dmc.Text("Random Seed", size="sm", fw=600, style={"marginBottom": "0.5rem"}),
                                            dmc.NumberInput(
                                                id="seed-community",
                                                value=42,
                                                min=0,
                                                step=1,
                                                style={"width": "100%"}
                                            ),
                                        ]
                                    ),
                                    dmc.GridCol(
                                        span=12,
                                        children=[
                                            dmc.Text("Epsilon (pseudo-count)", size="sm", fw=600, style={"marginBottom": "0.5rem"}),
                                            dmc.NumberInput(
                                                id="epsilon-community",
                                                value=1e-4,
                                                min=1e-10,
                                                max=1e-2,
                                                step=1e-5,
                                                placeholder="Enter epsilon value",
                                                style={"width": "100%"}
                                            ),
                                            dmc.Text(
                                                "Small pseudocount (ε) added to signature probabilities to reduce noise. Default: ε = 1e-4",
                                                size="xs",
                                                c="dimmed",
                                                style={"marginTop": "0.5rem"}
                                            ),
                                        ]
                                    ),
                                    dmc.GridCol(
                                        span=12,
                                        children=[
                                            dmc.Text("Community Resolution (Louvain)", size="sm", fw=600, style={"marginBottom": "0.5rem"}),
                                            dmc.Slider(
                                                id="resolution-community",
                                                value=1.0,
                                                min=0.3,
                                                max=3.0,
                                                step=0.1,
                                                marks=[
                                                    {"value": 0.3, "label": "Fewer, larger"},
                                                    {"value": 1.0, "label": "Default"},
                                                    {"value": 3.0, "label": "More, smaller"},
                                                ],
                                                style={"width": "100%", "marginBottom": "1.5rem"}
                                            ),
                                            dmc.Text(
                                                "Controls the modularity optimization's preference for community size. Default: 1.0",
                                                size="xs",
                                                c="dimmed",
                                                style={"marginTop": "0.5rem"}
                                            ),
                                        ]
                                    ),
                                    dmc.GridCol(
                                        span=12,
                                        children=[
                                            dmc.Text("Neighbours per Signature (k)", size="sm", fw=600, style={"marginBottom": "0.5rem"}),
                                            dmc.Slider(
                                                id="k-neighbours-community",
                                                value=DEFAULT_K,
                                                min=2,
                                                max=10,
                                                step=1,
                                                marks=[
                                                    {"value": 2, "label": "Sparse"},
                                                    {"value": DEFAULT_K, "label": "Default"},
                                                    {"value": 10, "label": "Dense"},
                                                ],
                                                style={"width": "100%", "marginBottom": "1.5rem"}
                                            ),
                                            dmc.Text(
                                                "Each signature is connected to its k most similar neighbours. Because the cutoff is per-signature "
                                                "rather than global, a tightly-packed family and a looser one can both hold together at the same k. "
                                                "Raise k if too many signatures sit alone; lower it if everything collapses into one community. "
                                                f"Default: k = {DEFAULT_K}",
                                                size="xs",
                                                c="dimmed",
                                                style={"marginTop": "0.5rem"}
                                            ),
                                        ]
                                    ),
                                    dmc.GridCol(
                                        span=12,
                                        children=[
                                            dmc.Switch(
                                                id="mutual-knn-community",
                                                checked=True,
                                                label="Mutual neighbours only",
                                                size="sm",
                                                style={"marginBottom": "0.5rem"}
                                            ),
                                            dmc.Text(
                                                "Keep an edge only when both signatures rank each other within their top k. This is the stricter, "
                                                "recommended setting: it stops a signature with no close relatives from attaching itself to a "
                                                "well-formed community. Turn it off for a denser, more connected graph.",
                                                size="xs",
                                                c="dimmed",
                                                style={"marginTop": "0.5rem"}
                                            ),
                                        ]
                                    ),
                                ],
                                grow=True,
                            ),
                        ]
                    ),
                ]
            ),

            html.Div(id='form-output-community'),

            # Graphs
            dmc.Grid(
                children=[
                    dmc.GridCol(
                        span=6,
                        children=[
                            dmc.Card(
                                style={
                                    "backgroundColor": COLORS["white"],
                                    "border": f"1px solid {COLORS['border']}",
                                    "boxShadow": COLORS["shadow"],
                                    "borderRadius": "0.75rem",
                                },
                                children=[
                                    html.H5("Signature Communities", style={"fontWeight": "600", "marginBottom": "1rem"}),
                                    dcc.Loading(
                                        id="loading-community-plot",
                                        type="default",
                                        children=dcc.Graph(
                                            id='community-graph-plot',
                                            figure=empty_community_fig("Click \"Detect Communities\" to run Louvain"),
                                            config={
                                                'displayModeBar': True,
                                                'displaylogo': False,
                                                'modeBarButtonsToAdd': ['toImage'],
                                                'toImageButtonOptions': {
                                                    'format': 'png',
                                                    'filename': 'signature_communities',
                                                    'height': 700,
                                                    'width': 900,
                                                    'scale': 2
                                                }
                                            }
                                        )
                                    ),
                                    html.Div(id='community-list-signatures', style={"marginTop": "1rem"}),
                                ]
                            ),
                        ]
                    ),
                    dmc.GridCol(
                        span=6,
                        children=[
                            dmc.Card(
                                style={
                                    "backgroundColor": COLORS["white"],
                                    "border": f"1px solid {COLORS['border']}",
                                    "boxShadow": COLORS["shadow"],
                                    "borderRadius": "0.75rem",
                                },
                                children=[
                                    html.H5("RePrint Communities", style={"fontWeight": "600", "marginBottom": "1rem"}),
                                    dcc.Loading(
                                        id="loading-community-reprint-plot",
                                        type="default",
                                        children=dcc.Graph(
                                            id='community-graph-reprint-plot',
                                            figure=empty_community_fig("Click \"Detect Communities\" to run Louvain"),
                                            config={
                                                'displayModeBar': True,
                                                'displaylogo': False,
                                                'modeBarButtonsToAdd': ['toImage'],
                                                'toImageButtonOptions': {
                                                    'format': 'png',
                                                    'filename': 'reprint_communities',
                                                    'height': 700,
                                                    'width': 900,
                                                    'scale': 2
                                                }
                                            }
                                        )
                                    ),
                                    html.Div(id='community-list-reprint', style={"marginTop": "1rem"}),
                                ]
                            ),
                        ]
                    ),
                ],
                gutter="md",
                grow=True,
            ),

            dcc.Store(id='community-assignments-store', data=None),
            dcc.Download(id="download-community-csv"),
        ]
    ),
])


# ============================================================================
# Upload / session-store callbacks (mirrors pages/page1.py)
# ============================================================================

def _as_lists(contents, filename):
    if not isinstance(contents, list):
        return [contents], [filename]
    return contents, filename


@app.callback(
    [Output('session-community-signatures', 'data')],
    [Input('upload-data-community', 'contents')],
    [State('upload-data-community', 'filename')]
)
def update_output_signatures_community(contents, filename):
    if contents is not None:
        contents_list, filenames_list = _as_lists(contents, filename)
        df_signatures, errors = merge_uploaded_signatures(contents_list, filenames_list)

        if df_signatures is None:
            return dash.no_update

        failed_names = {f for f, _ in errors}
        succeeded_names = [f for f in filenames_list if f not in failed_names]

        info = f"Merged {len(succeeded_names)} file(s): {', '.join(succeeded_names)}"
        return [{'signatures_data': df_signatures.to_dict('records'), 'filename': succeeded_names, 'info': info}]
    return dash.no_update


@app.callback(
    Output('upload-error-message-community', 'children'),
    Input('upload-data-community', 'contents'),
    State('upload-data-community', 'filename'),
    prevent_initial_call=True
)
def show_upload_status_community(contents, filename):
    if contents is None:
        return ""

    contents_list, filenames_list = _as_lists(contents, filename)
    _, errors = merge_uploaded_signatures(contents_list, filenames_list)
    failed_names = {f for f, _ in errors}
    succeeded_names = [f for f in filenames_list if f not in failed_names]

    alerts = []
    if succeeded_names:
        alerts.append(dmc.Alert(
            f"Successfully loaded and merged {len(succeeded_names)} file(s): {', '.join(succeeded_names)}",
            icon=DashIconify(icon="tabler:check-circle", width=18),
            title="Success",
            color="green",
            withCloseButton=True
        ))
    for fname, message in errors:
        alerts.append(dmc.Alert(
            f"Error while processing file '{fname}': {message}",
            icon=DashIconify(icon="tabler:alert-circle", width=18),
            title="Error",
            color="red",
            withCloseButton=True
        ))
    return alerts


@app.callback(
    [Output('session-community-signatures', 'data', allow_duplicate=True),
     Output('upload-error-message-community', 'children', allow_duplicate=True),
     Output('auto-reload-armed-community', 'data', allow_duplicate=True)],
    Input('load-example-btn-community', 'n_clicks'),
    prevent_initial_call=True,
)
def load_example_dataset_community(n_clicks):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update

    label = EXAMPLE_SIGNATURE_SETS[DEFAULT_EXAMPLE_SET]['label']
    filenames = DEFAULT_EXAMPLE_STORE['filename']
    alert = dmc.Alert(
        f"Loaded {label} — {len(filenames)} files merged into "
        f"{len(DEFAULT_EXAMPLE_SIGNATURES)} profiles: {', '.join(filenames)}",
        icon=DashIconify(icon="tabler:check-circle", width=18),
        title="Example Loaded",
        color="blue",
        withCloseButton=True
    )
    return DEFAULT_EXAMPLE_STORE, alert, True


@app.callback(
    [Output('session-community-signatures', 'data', allow_duplicate=True),
     Output('upload-data-community', 'contents'),
     Output('upload-error-message-community', 'children', allow_duplicate=True),
     Output('auto-reload-armed-community', 'data', allow_duplicate=True)],
    Input('clear-upload-btn-community', 'n_clicks'),
    prevent_initial_call=True,
)
def clear_uploaded_signatures_community(n_clicks):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    return None, None, '', True


@app.callback(
    Output('reload-signal-community', 'data'),
    Output('auto-reload-armed-community', 'data', allow_duplicate=True),
    Input('signatures-dropdown-community', 'value'),
    State('auto-reload-armed-community', 'data'),
    State('reload-signal-community', 'data'),
    prevent_initial_call=True,
)
def fire_auto_reload_community(_, armed, signal):
    if not armed:
        return dash.no_update, dash.no_update
    return (signal or 0) + 1, False


@app.callback(
    Output("collapse-form-community", "opened"),
    [Input("toggle-button-community", "n_clicks")],
    [State("collapse-form-community", "opened")],
)
def toggle_collapse_community(n, is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    [Output('signatures-dropdown-community', 'options'),
     Output('signatures-dropdown-community', 'value'),
     Output('dropdown-community', 'style'),
     Output('info_uploader-community', 'children'),
     Output('clear-upload-btn-community', 'style'),
     Output('clear-upload-hint-community', 'style'),
     ],
    [Input('dropdown-community', 'value'),
     Input('session-community-signatures', 'data')]
)
def set_options_community(selected_category, contents):
    if contents is not None:
        df = pd.DataFrame(contents['signatures_data'])
        df.index = df['Type']
        df = df.drop(columns='Type')
        signatures = df.columns.to_list()
        return (
            [{'label': signature, 'value': signature} for signature in signatures],
            signatures,
            {'display': 'None'},
            '',
            {"marginTop": "1rem", "display": "inline-block"},
            {"marginTop": "0.25rem", "display": "block"})

    return ([{'label': f"{i}", 'value': i} for i in data[selected_category]],
            [i for i in data[selected_category]],
            {'display': 'block'},
            'Not Uploaded',
            {"marginTop": "1rem", "display": "none"},
            {"marginTop": "0.25rem", "display": "none"})


@app.callback(
    [Output("active-file-display-community", "children"),
     Output("signature-count-community", "children")],
    [Input("dropdown-community", "value"),
     Input("session-community-signatures", "data")]
)
def update_active_file_display_community(selected_file, session_contents):
    if session_contents is not None:
        df = pd.DataFrame(session_contents["signatures_data"])
        sig_cols = [c for c in df.columns if c != "Type"]
        uploaded_names = session_contents["filename"]
        uploaded_names = uploaded_names if isinstance(uploaded_names, list) else [uploaded_names]
        return ", ".join(uploaded_names), f"{len(sig_cols)} signatures"
    if selected_file and selected_file in data:
        return selected_file, f"{len(data[selected_file])} signatures"
    return "None", "0"


# ============================================================================
# Community detection
# ============================================================================

def _community_badges(communities):
    """A small colored badge per community, listing its members, for the
    area under each graph."""
    from utils.community import COMMUNITY_COLORS

    if not communities:
        return ''

    items = []
    for cid, members in enumerate(communities, start=1):
        color = COMMUNITY_COLORS[(cid - 1) % len(COMMUNITY_COLORS)]
        items.append(
            dmc.Group(
                gap="xs",
                align="flex-start",
                wrap="nowrap",
                style={"marginBottom": "0.4rem"},
                children=[
                    dmc.Badge(f"#{cid} (n={len(members)})", color="gray", variant="filled",
                               style={"backgroundColor": color, "flexShrink": 0}),
                    dmc.Text(", ".join(sorted(members)), size="xs", c=COLORS["text_secondary"]),
                ]
            )
        )
    return items


@app.callback(
    [Output('form-output-community', 'children'),
     Output('community-graph-plot', 'figure'),
     Output('community-graph-reprint-plot', 'figure'),
     Output('community-list-signatures', 'children'),
     Output('community-list-reprint', 'children'),
     Output('community-assignments-store', 'data')],
    [Input('initial-load-community', 'n_intervals'),
     Input('reload-signal-community', 'data'),
     Input('submit-button-community', 'n_clicks')],
    [State('dropdown-community', 'value'),
     State('signatures-dropdown-community', 'value'),
     State('distance-metric-community', 'value'),
     State('epsilon-community', 'value'),
     State('resolution-community', 'value'),
     State('k-neighbours-community', 'value'),
     State('mutual-knn-community', 'checked'),
     State('seed-community', 'value'),
     State('session-community-signatures', 'data'),
     ],
    running=[
        (Output('submit-button-community', 'loading'), True, False),
        (Output('submit-button-community', 'disabled'), True, False),
    ],
)
def update_community_output(init_load, reload_signal, n_clicks, selected_file, selected_signatures,
                             distance_metric, epsilon, resolution, k_neighbours, mutual, seed, signatures):
    if not selected_signatures or not selected_file:
        return '', dash.no_update, dash.no_update, '', '', dash.no_update

    calc_func = DISTANCE_FUNCTIONS[distance_metric]
    seed = int(seed) if seed is not None else 42
    k_neighbours = int(k_neighbours) if k_neighbours else DEFAULT_K
    mutual = bool(mutual)

    if signatures is not None:
        data_df = pd.DataFrame(signatures['signatures_data'])
        data_df.index = data_df['Type']
        data_df = data_df.drop(columns='Type')[selected_signatures]
    else:
        data_df = pd.read_csv(f"data/signatures/{selected_file}", sep='\t', index_col=0)[selected_signatures]

    df_reprint = reprint(data_df, epsilon=epsilon)

    G_sig, communities_sig, community_of_sig, mod_sig = detect_communities(
        data_df, calc_func=calc_func, resolution=resolution, k=k_neighbours, mutual=mutual, seed=seed)
    G_rep, communities_rep, community_of_rep, mod_rep = detect_communities(
        df_reprint, calc_func=calc_func, resolution=resolution, k=k_neighbours, mutual=mutual, seed=seed)

    fig_sig = create_community_graph_figure(G_sig, communities_sig, mod_sig, seed=seed, title="Signatures")
    fig_rep = create_community_graph_figure(G_rep, communities_rep, mod_rep, seed=seed, title="RePrints")

    assignments = {
        'Signature': selected_signatures,
        'Community_Signatures': [community_of_sig.get(s) for s in selected_signatures],
        'Community_RePrint': [community_of_rep.get(s) for s in selected_signatures],
    }

    summary = (f"Distance Metric: {distance_metric}, Resolution: {resolution}, "
               f"Neighbours (k): {k_neighbours}"
               f"{' mutual' if mutual else ''}, Seed: {seed}")

    return (summary, fig_sig, fig_rep,
            _community_badges(communities_sig), _community_badges(communities_rep),
            assignments)


@app.callback(
    [Output('community-graph-plot', 'figure', allow_duplicate=True),
     Output('community-graph-reprint-plot', 'figure', allow_duplicate=True)],
    [Input('distance-metric-community', 'value'),
     Input('epsilon-community', 'value'),
     Input('resolution-community', 'value'),
     Input('k-neighbours-community', 'value'),
     Input('mutual-knn-community', 'checked'),
     Input('seed-community', 'value')],
    prevent_initial_call=True
)
def clear_plots_on_parameter_change_community(*_):
    msg = "Click \"Detect Communities\" to apply the new parameters"
    return empty_community_fig(msg), empty_community_fig(msg)


@app.callback(
    [Output('community-graph-plot', 'figure', allow_duplicate=True),
     Output('community-graph-reprint-plot', 'figure', allow_duplicate=True)],
    Input('signatures-dropdown-community', 'value'),
    prevent_initial_call=True
)
def clear_plots_on_signature_change_community(selected_signatures):
    msg = "Click \"Detect Communities\" to apply the new selection"
    return empty_community_fig(msg), empty_community_fig(msg)


@app.callback(
    [Output('community-graph-plot', 'figure', allow_duplicate=True),
     Output('community-graph-reprint-plot', 'figure', allow_duplicate=True)],
    Input('dropdown-community', 'value'),
    prevent_initial_call=True
)
def clear_plots_on_file_change_community(selected_file):
    msg = "Click \"Detect Communities\" to apply the new file"
    return empty_community_fig(msg), empty_community_fig(msg)


@app.callback(
    [Output('community-graph-plot', 'figure', allow_duplicate=True),
     Output('community-graph-reprint-plot', 'figure', allow_duplicate=True)],
    Input('session-community-signatures', 'data'),
    prevent_initial_call=True
)
def clear_plots_on_upload_community(uploaded_data):
    if uploaded_data is not None:
        msg = "Click \"Detect Communities\" to apply the uploaded data"
        return empty_community_fig(msg), empty_community_fig(msg)
    return dash.no_update, dash.no_update


@app.callback(
    Output("download-community-csv", "data"),
    Input("btn_csv-community", "n_clicks"),
    State('community-assignments-store', 'data'),
    prevent_initial_call=True
)
def download_community_csv(n_clicks, assignments):
    if not assignments:
        return dash.no_update
    df = pd.DataFrame(assignments)
    return dcc.send_data_frame(df.to_csv, filename="community_assignments.csv", index=False)
