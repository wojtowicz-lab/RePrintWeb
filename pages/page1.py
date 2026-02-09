from utils.figpanel import create_heatmap_with_custom_sim
from utils.utils import FILES, DEFAULT_SIGNATURES, linkage_methods, DEFAULT_LINKAGE_METHOD, reprint, calculate_rmse, calculate_cosine, calculate_js_divergence
from main import app
from dash import dcc, html, Input, Output, State, ctx, ALL
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from pages.nav import navbar
import pandas as pd
import plotly.graph_objects as go




data = {}
for file in FILES:
    data[file] = pd.read_csv(f'data/signatures/{file}', sep='\t').columns[1:].to_list()

dropdown_options = [{'label': file, 'value': file} for file in FILES]


# ============================================================================
# STYLING CONFIGURATION
# ============================================================================
COLORS = {
    "primary_blue": "#2563EB",      # Deep Royal Blue (Header)
    "primary_dark": "#1e40af",      # Darker Blue
    "bg_light": "#F8FAFC",          # Very light grey (Background)
    "bg_lighter": "#F0F5FB",        # Even lighter blue-ish background
    "white": "#FFFFFF",             # Pure white (Cards)
    "navy": "#1E293B",              # Dark Navy (Advanced Options)
    "teal": "#14B8A6",              # Teal/Green (Download)
    "red": "#E11D48",               # Vibrant Red (Reload Heatmaps)
    "text_primary": "#1F2937",      # Dark text
    "text_secondary": "#6B7280",    # Secondary text
    "border": "#E5E7EB",            # Light border
    "shadow": "0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04)",
    "shadow_md": "0 4px 12px rgba(0, 0, 0, 0.12), 0 2px 6px rgba(0, 0, 0, 0.06)",
}

# ============================================================================
# APPLICATION LAYOUT
# ============================================================================
page1_layout = html.Div([
    navbar,
    
    # Main Container with light grey background
    dmc.Container(
        size="xl",
        style={"backgroundColor": COLORS["bg_light"], "minHeight": "100vh", "paddingTop": "3rem", "paddingBottom": "3rem"},
        children=[
            # Instructions Section - Accordion
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
                                                DashIconify(icon="tabler:info-circle", width=20, height=20, color=COLORS["primary_blue"]),
                                                html.H5("How to Use This Dashboard", style={"margin": 0, "fontWeight": "600"}),
                                            ]
                                        ),
                                    ),
                                    dmc.AccordionPanel(
                                        children=dmc.Grid(
                                        children=[
                                            # Workflow Steps Column
                                            dmc.GridCol(
                                                span=4,
                                                children=[
                                                    html.H6("1. Workflow Steps", style={"fontWeight": "600", "marginBottom": "1rem"}),
                                                    html.Ol(
                                                        [
                                                            html.Li("Select a reference signature file from the first dropdown (e.g., COSMIC).", style={"marginBottom": "0.75rem"}),
                                                            html.Li("Optionally upload your own query signatures using the drag-and-drop box.", style={"marginBottom": "0.75rem"}),
                                                            html.Li("Adjust advanced options (distance metric, clustering, epsilon), if needed.", style={"marginBottom": "0.75rem"}),
                                                            html.Li([
                                                                html.Strong("Click "), "the ",
                                                                html.Strong("Reload heatmaps"),
                                                                " button to generate the analysis and update the plots."
                                                            ]),
                                                        ],
                                                        style={"fontSize": "0.95rem", "color": COLORS["text_primary"]}
                                                    ),
                                                ]
                                            ),
                                            # Distance Metrics Column
                                            dmc.GridCol(
                                                span=4,
                                                children=[
                                                    html.H6("2. Distance Metrics", style={"fontWeight": "600", "marginBottom": "1rem"}),
                                                    html.Ul([
                                                        html.Li(
                                                            [html.Strong("Cosine: "), "Measures angular similarity between signatures"],
                                                            style={"marginBottom": "0.75rem", "fontSize": "0.95rem", "color": COLORS["text_primary"]}
                                                        ),
                                                        html.Li(
                                                            [html.Strong("RMSE: "), "Root mean square error between normalized signatures"],
                                                            style={"marginBottom": "0.75rem", "fontSize": "0.95rem", "color": COLORS["text_primary"]}
                                                        ),
                                                        html.Li(
                                                            [html.Strong("JS Divergence: "), "Jensen-Shannon divergence (symmetric version of Kullback-Leibler divergence)"],
                                                            style={"fontSize": "0.95rem", "color": COLORS["text_primary"]}
                                                        ),
                                                    ], style={"paddingLeft": "1.5rem"}),
                                                ]
                                            ),
                                            # Downloads Column
                                            dmc.GridCol(
                                                span=4,
                                                children=[
                                                    html.H6("3. Downloads", style={"fontWeight": "600", "marginBottom": "1rem"}),
                                                    html.Ul([
                                                        html.Li(
                                                            "Download RePrint matrix as CSV",
                                                            style={"marginBottom": "0.75rem", "fontSize": "0.95rem", "color": COLORS["text_primary"]}
                                                        ),
                                                        html.Li(
                                                            "Download original signature matrix",
                                                            style={"fontSize": "0.95rem", "color": COLORS["text_primary"]}
                                                        ),
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
            
            # Actions Toolbar
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
                                id="toggle-button",
                                color="dark",
                                size="md",
                                style={"backgroundColor": COLORS["navy"]},
                                leftSection=DashIconify(icon="tabler:adjustments", width=18),
                            ),
                            dmc.Button(
                                "Download Reprints",
                                id="btn_csv-1",
                                color="teal",
                                size="md",
                                style={"backgroundColor": COLORS["teal"]},
                                leftSection=DashIconify(icon="tabler:download", width=18),
                            ),
                            dmc.Button(
                                "Download Signatures",
                                id="btn_csv-signatures",
                                color="gray",
                                size="md",
                                leftSection=DashIconify(icon="tabler:download", width=18),
                            ),
                            dmc.Button(
                                "Reload Heatmaps",
                                id="submit-button",
                                color="red",
                                size="md",
                                style={"backgroundColor": COLORS["red"]},
                                leftSection=DashIconify(icon="tabler:reload", width=18),
                            ),
                        ]
                    ),
                ]
            ),
            
            # Advanced Options Collapse
            dmc.Collapse(
                opened=False,
                id="collapse-form",
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
                                                id='distance-metric',
                                                options=[
                                                    {'label': 'Cosine', 'value': 'cosine'},
                                                    {'label': 'RMSE', 'value': 'rmse'},
                                                    {'label': 'JS Divergence', 'value': 'js_divergence'}
                                                ],
                                                value='rmse',
                                                style={"width": "100%"}
                                            ),
                                        ]
                                    ),
                                    dmc.GridCol(
                                        span=6,
                                        children=[
                                            dmc.Text("Clustering Method", size="sm", fw=600, style={"marginBottom": "0.5rem"}),
                                            dcc.Dropdown(
                                                id='clustering-method',
                                                options=[{'label': method.title(), 'value': method} for method in linkage_methods],
                                                value=DEFAULT_LINKAGE_METHOD,
                                                clearable=False,
                                                style={"width": "100%"}
                                            ),
                                        ]
                                    ),
                                    dmc.GridCol(
                                        span=12,
                                        children=[
                                            dmc.Text("Epsilon (pseudo-count)", size="sm", fw=600, style={"marginBottom": "0.5rem"}),
                                            dmc.NumberInput(
                                                id="epsilon",
                                                value=1e-4,
                                                min=1e-10,
                                                max=1e-2,
                                                step=1e-5,
                                                placeholder="Enter epsilon value",
                                                style={"width": "100%"}
                                            ),
                                            dmc.Text(
                                                "Small pseudocount (ε) added to signature probabilities to reduce noise and avoid missing values due to rare mutations. Default: ε = 1e-4",
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
            
            html.Div(id='form-output'),
            
            # File Selection and Signature Management Section
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
                    # Active Reference File Card
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
                                                    dmc.Text(id="active-file-display-1", size="md", fw=700, style={"color": COLORS["text_primary"]}),
                                                    dmc.Badge(id="signature-count-1", size="sm", color="blue", variant="light"),
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
                    
                    # Reference File Selection
                    dmc.Stack(
                        children=[
                            dmc.Group(
                                children=[
                                    dmc.Text("Change Reference File", size="sm", fw=600),
                                ],
                                justify="space-between",
                            ),
                            dcc.Dropdown(
                                id='dropdown-1',
                                options=dropdown_options,
                                value=DEFAULT_SIGNATURES,
                            ),
                        ],
                        gap="xs",
                    ),
                    
                    html.Div(style={"marginTop": "2rem"}),
                    
                    # Signature Search and Selection
                    dmc.Stack(
                        children=[
                            dmc.Group(
                                children=[
                                    dmc.Text("Select Signatures", size="sm", fw=600),
                                    dmc.Group(
                                        children=[
                                            dmc.Button("Add All", id="add-all-btn-1", size="xs", variant="light", color="blue"),
                                            dmc.Button("Clear All", id="clear-all-btn-1", size="xs", variant="light", color="gray"),
                                        ],
                                        gap="xs",
                                    ),
                                ],
                                justify="space-between",
                            ),
                            
                            # Search bar
                            dmc.TextInput(
                                id="signature-search-1",
                                placeholder="Search signatures...",
                                leftSection=DashIconify(icon="tabler:search", width=18),
                                style={"marginBottom": "1rem"},
                            ),
                            
                            # Signature Chips/Badges
                            html.Div(
                                id="signatures-chips-container-1",
                                style={
                                    "display": "flex",
                                    "flexWrap": "wrap",
                                    "gap": "0.75rem",
                                    "padding": "1rem",
                                    "backgroundColor": "#F8FAFC",
                                    "borderRadius": "0.5rem",
                                    "border": f"1px solid {COLORS['border']}",
                                    "minHeight": "120px",
                                    "alignContent": "flex-start",
                                }
                            ),
                        ],
                        gap="md",
                    ),
                    
                    # Hidden store for tracking selected signatures
                    dcc.Store(id="selected-signatures-store-1", data=[k for k in data[DEFAULT_SIGNATURES]]),
                    
                    # Hidden dropdown - kept in sync with chips, used by other callbacks
                    html.Div(
                        dcc.Dropdown(
                            id='signatures-dropdown-1',
                            options=[{'label': k, 'value': k} for k in data.keys()],
                            multi=True,
                            value=[k for k in data[DEFAULT_SIGNATURES]],
                        ),
                        style={"display": "none"}
                    ),
                ]
            ),
            
            # File Format Instructions
            dmc.Card(
                style={
                    "backgroundColor": "#F0F9FF",
                    "border": f"1px solid #BFDBFE",
                    "borderRadius": "0.75rem",
                    "marginBottom": "2.5rem",
                    "padding": "2rem",
                },
                children=[
                    html.Div(
                        style={"display": "flex", "gap": "1rem", "alignItems": "flex-start"},
                        children=[
                            DashIconify(icon="tabler:info-circle", width=20, height=20, color="#0369A1", style={"flexShrink": 0, "marginTop": "0.25rem"}),
                            html.Div(
                                children=[
                                    html.H5("Expected File Format", style={"fontWeight": "600", "marginTop": 0, "marginBottom": "0.75rem"}),
                                    html.P(
                                        "The uploaded file should be a tab-separated file (.txt) containing mutation types and corresponding mutation signatures.",
                                        style={"fontSize": "0.95rem", "marginBottom": "0.75rem"}
                                    ),
                                    html.P("Columns:", style={"fontSize": "0.95rem", "marginBottom": "0.5rem", "fontWeight": "600"}),
                                    html.Ul([
                                        html.Li("Type: Mutation type (e.g., A[C>A]A, A[C>A]C, ...)", style={"fontSize": "0.9rem"}),
                                        html.Li("SBS1, SBS2, ..., SBSN: Signature mutation values (frequencies or probabilities)", style={"fontSize": "0.9rem"})
                                    ], style={"paddingLeft": "1.5rem", "marginBottom": "0.75rem"}),
                                    html.P("Example first few rows:", style={"fontSize": "0.95rem", "marginBottom": "0.5rem", "fontWeight": "600"}),
                                    html.Pre(
                                        "Type\tSBS1\tSBS2\tSBS3\n"
                                        "A[C>A]A\t0.001\t0.002\t0.003\n"
                                        "A[C>A]C\t0.004\t0.005\t0.006",
                                        style={
                                            "whiteSpace": "pre-wrap",
                                            "fontFamily": "monospace",
                                            "fontSize": "0.85rem",
                                            "backgroundColor": "white",
                                            "padding": "0.75rem",
                                            "borderRadius": "0.375rem",
                                            "border": f"1px solid {COLORS['border']}",
                                            "overflow": "auto",
                                            "marginBottom": 0
                                        }
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            ),
            
            # File Upload Area
            dmc.Card(
                style={
                    "backgroundColor": COLORS["white"],
                    "border": f"2px dashed {COLORS['primary_blue']}",
                    "borderRadius": "0.75rem",
                    "marginBottom": "2.5rem",
                    "padding": "3rem 2rem",
                    "textAlign": "center",
                    "cursor": "pointer",
                    "transition": "all 0.3s ease",
                    "background": f"linear-gradient(135deg, {COLORS['white']} 0%, {COLORS['bg_lighter']} 100%)",
                },
                children=[
                    dcc.Upload(
                        id='upload-data-1-signatures',
                        children=html.Div([
                            DashIconify(icon="tabler:cloud-upload", width=40, height=40, color=COLORS["primary_blue"], style={"marginBottom": "0.75rem"}),
                            html.P("Drag and drop your signature file here, or click to select", style={"fontSize": "1rem", "fontWeight": "500"}),
                            html.P("Accepted format: .txt (tab-separated)", style={"fontSize": "0.85rem", "color": COLORS["text_secondary"]})
                        ]),
                        multiple=False,
                        style={
                            "width": "100%",
                            "cursor": "pointer",
                        }
                    ),
                ]
            ),
            
            html.Div(id='upload-error-message-1'),
            html.Div(id='info_uploader'),
            dcc.Store(id='session-1-signatures', storage_type='session', data=None),
            
            # Hide Heatmap Toggle
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
                        children=[
                            dmc.Text("Hide Heatmap Visualization", size="md", fw=600),
                            dmc.Switch(
                                id="toggle-heatmap",
                                checked=False,
                                onLabel="OFF",
                                offLabel="ON",
                            ),
                        ],
                        justify="space-between",
                    ),
                ]
            ),
            
            # Heatmaps Grid
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
                                    html.H5("Signature Similarity", style={"fontWeight": "600", "marginBottom": "1rem"}),
                                    dcc.Loading(
                                        id="loading-heatmap-plot",
                                        type="default",
                                        children=dcc.Graph(
                                            id='heatmap-plot',
                                            config={
                                                'displayModeBar': True,
                                                'displaylogo': False,
                                                'modeBarButtonsToAdd': ['toImage'],
                                                'toImageButtonOptions': {
                                                    'format': 'png',
                                                    'filename': 'signature_similarity_heatmap',
                                                    'height': 600,
                                                    'width': 800,
                                                    'scale': 2
                                                }
                                            }
                                        )
                                    )
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
                                    html.H5("RePrint Similarity", style={"fontWeight": "600", "marginBottom": "1rem"}),
                                    dcc.Loading(
                                        id="loading-heatmap-reprint-plot",
                                        type="default",
                                        children=dcc.Graph(
                                            id='heatmap-reprint-plot',
                                            config={
                                                'displayModeBar': True,
                                                'displaylogo': False,
                                                'modeBarButtonsToAdd': ['toImage'],
                                                'toImageButtonOptions': {
                                                    'format': 'png',
                                                    'filename': 'reprint_similarity_heatmap',
                                                    'height': 600,
                                                    'width': 800,
                                                    'scale': 2
                                                }
                                            }
                                        )
                                    )
                                ]
                            ),
                        ]
                    ),
                ],
                gutter="md",
                grow=True,
            ),
            
            dcc.Location(id='url-page1', refresh=False),
            dcc.Download(id="download-dataframe-csv-1"),
            dcc.Download(id="download-dataframe-csv-signatures")
        ]
    ),
])

from utils.utils import parse_signatures
import dash

@app.callback(
    [Output('session-1-signatures', 'data')],
    [Input('upload-data-1-signatures', 'contents')],
    [State('upload-data-1-signatures', 'filename')]
)
def update_output_signatures(contents, filename):
    if contents is not None:
        df_signatures = parse_signatures(contents, filename)

        signatures_info = "Some information extracted from df_signatures"
        return [{'signatures_data': df_signatures.to_dict('records'), 'filename': filename, 'info': signatures_info}]
    else:
        return dash.no_update

@app.callback(
    Output('upload-error-message-1', 'children'),
    Input('upload-data-1-signatures', 'contents'),
    State('upload-data-1-signatures', 'filename'),
    prevent_initial_call=True
)
def show_upload_status(contents, filename):
    if contents is not None:
        try:
            _ = parse_signatures(contents, filename)
            return dmc.Alert(
                f"Successfully loaded file: {filename}",
                icon=DashIconify(icon="tabler:check-circle", width=18),
                title="Success",
                color="green",
                withCloseButton=True
            )
        except Exception as e:
            return dmc.Alert(
                f"Error while processing file '{filename}'",
                icon=DashIconify(icon="tabler:alert-circle", width=18),
                title="Error",
                color="red",
                withCloseButton=True
            )
    return ""

@app.callback(
    Output("collapse-form", "opened"),
    [Input("toggle-button", "n_clicks")],
    [State("collapse-form", "opened")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open



@app.callback(
    [Output('form-output', 'children'),
     Output('heatmap-plot', 'figure'),
     Output('heatmap-reprint-plot', 'figure')],
    [Input('submit-button', 'n_clicks'),
     Input("toggle-heatmap", "checked")],
    [State('dropdown-1', 'value'),
     State('signatures-dropdown-1', 'value'),
     State('distance-metric', 'value'),
     State('clustering-method', 'value'),
     State('epsilon', 'value'),
     State('session-1-signatures', 'data'),
     ]
)
def update_output(n_clicks, hide_heatmap, selected_file, selected_signatures, distance_metric, clustering_method, epsilon, signatures):
    if n_clicks:
        if signatures is not None:
            data = pd.DataFrame(signatures['signatures_data'])
            data.index = data['Type']
            data = data.drop(columns='Type')[selected_signatures]
            functions = {'rmse': calculate_rmse, 'cosine': calculate_cosine, 'js_divergence': calculate_js_divergence}
            df_reprint = reprint(data, epsilon=epsilon)
            return (f'Submitted: Distance Metric: {distance_metric}, Clustering Method: {clustering_method}, Epsilon: {epsilon}',
                    create_heatmap_with_custom_sim(data, calc_func=functions[distance_metric], colorscale='YlGnBu', hide_heatmap=hide_heatmap, method=clustering_method),
                    create_heatmap_with_custom_sim(df_reprint, calc_func=functions[distance_metric], colorscale='OrRd', hide_heatmap=hide_heatmap, method=clustering_method)
                    )
        else:
            df_signatures = pd.read_csv(f"data/signatures/{selected_file}", sep='\t', index_col=0)[selected_signatures]
            functions = {'rmse': calculate_rmse, 'cosine': calculate_cosine, 'js_divergence': calculate_js_divergence}
            df_reprint = reprint(df_signatures, epsilon=epsilon)
            return (f'Submitted: Distance Metric: {distance_metric}, Clustering Method: {clustering_method}, Epsilon: {epsilon}',
                    create_heatmap_with_custom_sim(df_signatures, calc_func=functions[distance_metric], colorscale='YlGnBu', hide_heatmap=hide_heatmap, method=clustering_method),
                    create_heatmap_with_custom_sim(df_reprint, calc_func=functions[distance_metric], colorscale='OrRd', hide_heatmap=hide_heatmap, method=clustering_method)
                    )
    else:
        if signatures is not None:
            data = pd.DataFrame(signatures['signatures_data'])
            data.index = data['Type']
            data = data.drop(columns='Type')[selected_signatures]
            functions = {'rmse': calculate_rmse, 'cosine': calculate_cosine, 'js_divergence': calculate_js_divergence}
            df_reprint = reprint(data, epsilon=epsilon)
            return (f'Submitted: Distance Metric: {distance_metric}, Clustering Method: {clustering_method}, Epsilon: {epsilon}',
                    create_heatmap_with_custom_sim(data, calc_func=functions[distance_metric], colorscale='YlGnBu', hide_heatmap=hide_heatmap, method=clustering_method),
                    create_heatmap_with_custom_sim(df_reprint, calc_func=functions[distance_metric], colorscale='OrRd', hide_heatmap=hide_heatmap, method=clustering_method)
                    )
        else:
            df_signatures = pd.read_csv(f"data/signatures/{selected_file}", sep='\t', index_col=0)[selected_signatures]
            df_reprint = reprint(df_signatures, epsilon=epsilon)
            return (f'Distance Metric: {distance_metric}, Clustering Method: {clustering_method}, Epsilon: {epsilon}',
                    create_heatmap_with_custom_sim(df_signatures, colorscale='YlGnBu', hide_heatmap=hide_heatmap, method=clustering_method),
                    create_heatmap_with_custom_sim(df_reprint, colorscale='OrRd', hide_heatmap=hide_heatmap, method=clustering_method)
                    )

@app.callback(
    [Output('signatures-dropdown-1', 'options'),
     Output('signatures-dropdown-1', 'value'),
     Output('dropdown-1', 'style'),
     Output('info_uploader', 'children')
     ],
    [Input('dropdown-1', 'value'),
     Input('session-1-signatures', 'data')]
)
def set_options(selected_category, contents):
    if contents is not None:
        df = pd.DataFrame(contents['signatures_data'])
        df.index = df['Type']
        df = df.drop(columns='Type')
        signatures = df.columns.to_list()
        return (
            [{'label': signature, 'value': signature} for signature in signatures],
            signatures,
            {'display': 'None'},
            f'Added your signatures {contents["filename"]}')

    return ([{'label': f"{i}", 'value': i} for i in data[selected_category]],
            [i for i in data[selected_category]],
            {'display': 'block'},
            'Not Uploaded')


@app.callback(
    Output("download-dataframe-csv-1", "data"),
    Input("btn_csv-1", "n_clicks"),
    [State('signatures-dropdown-1', 'value'),
     State('dropdown-1', 'value'),
     State('epsilon', 'value'),
     State('session-1-signatures', 'data')],
    prevent_initial_call=True
)
def download_dataframe(n_clicks, selected_signatures, selected_file, epsilon, contents):
    if contents is not None:
        df_signatures = pd.DataFrame(contents['signatures_data'])
        df_signatures.index = df_signatures['Type']
        df_signatures = df_signatures.drop(columns='Type')[selected_signatures]
        df_reprint = reprint(df_signatures, epsilon=epsilon)

        df_reprint.columns = [f"reprint_{col}" for col in df_reprint.columns]

        return dcc.send_data_frame(df_reprint.to_csv, filename="reprints.csv")
    else:
        df_signatures = pd.read_csv(f"data/signatures/{selected_file}", sep='\t', index_col=0)[selected_signatures]
        df_reprint = reprint(df_signatures, epsilon=epsilon)

        df_reprint.columns = [f"reprint_{col}" for col in df_reprint.columns]

        return dcc.send_data_frame(df_reprint.to_csv, filename="reprints.csv")


from dash import dcc, Input, Output, State
import pandas as pd

@app.callback(
    Output("download-dataframe-csv-signatures", "data"),
    Input("btn_csv-signatures", "n_clicks"),
    [State('signatures-dropdown-1', 'value'),
     State('dropdown-1', 'value'),
     State('session-1-signatures', 'data')],
    prevent_initial_call=True
)
def download_signatures_only(n_clicks, selected_signatures, selected_file, contents):
    if contents is not None:
        # data from session
        df_signatures = pd.DataFrame(contents['signatures_data'])
        df_signatures.index = df_signatures['Type']
        df_signatures = df_signatures.drop(columns='Type')[selected_signatures]
    else:
        # data from file
        df_signatures = pd.read_csv(f"data/signatures/{selected_file}", sep='\t', index_col=0)[selected_signatures]

    return dcc.send_data_frame(df_signatures.to_csv, filename="signatures.csv")


# ============================================================================
# New Callbacks for Enhanced Signature Selection UI
# ============================================================================

@app.callback(
    [Output("active-file-display-1", "children"),
     Output("signature-count-1", "children")],
    [Input("dropdown-1", "value"),
     Input("session-1-signatures", "data")]
)
def update_active_file_display(selected_file, session_contents):
    """Update the active file display and signature count (from upload or dropdown)"""
    if session_contents is not None:
        df = pd.DataFrame(session_contents["signatures_data"])
        sig_cols = [c for c in df.columns if c != "Type"]
        return session_contents["filename"], f"{len(sig_cols)} signatures"
    if selected_file and selected_file in data:
        count = len(data[selected_file])
        return selected_file, f"{count} signatures"
    return "None", "0"


@app.callback(
    [Output("signatures-chips-container-1", "children"),
     Output("selected-signatures-store-1", "data")],
    [Input("dropdown-1", "value"),
     Input("session-1-signatures", "data"),
     Input("signature-search-1", "value"),
     Input("add-all-btn-1", "n_clicks"),
     Input("clear-all-btn-1", "n_clicks"),
     Input("selected-signatures-store-1", "data")],
    prevent_initial_call=False
)
def update_signature_chips(selected_file, session_contents, search_value, add_clicks, clear_clicks, selected_sigs):
    """Generate signature chips based on file/session and search/filter"""
    if session_contents is not None:
        df = pd.DataFrame(session_contents["signatures_data"])
        all_sigs = [c for c in df.columns if c != "Type"]
    elif selected_file and selected_file in data:
        all_sigs = data[selected_file]
    else:
        return [], []
    
    # Initialize selected_sigs if None
    if selected_sigs is None:
        selected_sigs = all_sigs.copy()
    
    # Handle "Add All" button
    if add_clicks and ctx.triggered_id == "add-all-btn-1":
        selected_sigs = all_sigs.copy()
    
    # Handle "Clear All" button
    if clear_clicks and ctx.triggered_id == "clear-all-btn-1":
        selected_sigs = []
    
    # Filter by search value
    filtered_sigs = all_sigs
    if search_value:
        search_lower = search_value.lower()
        filtered_sigs = [s for s in all_sigs if search_lower in s.lower()]
    
    # Create chips
    chips = []
    for sig in filtered_sigs:
        is_selected = sig in selected_sigs
        chip = dmc.Button(
            sig,
            id={"type": "sig-chip-1", "index": sig},
            color="blue" if is_selected else "gray",
            variant="filled" if is_selected else "light",
            size="xs",
            style={"cursor": "pointer", "fontSize": "0.9rem", "fontWeight": "500", "padding": "0.25rem 0.75rem"},
            n_clicks=0,
        )
        chips.append(chip)
    
    return chips, selected_sigs


@app.callback(
    Output("selected-signatures-store-1", "data", allow_duplicate=True),
    Input({"type": "sig-chip-1", "index": ALL}, "n_clicks"),
    [State("selected-signatures-store-1", "data"),
     State("dropdown-1", "value"),
     State("session-1-signatures", "data"),
     State("signature-search-1", "value")],
    prevent_initial_call=True
)
def toggle_signature_chip(n_clicks, selected_sigs, selected_file, session_contents, search_value):
    """Handle individual chip clicks to toggle selection. Use n_clicks index to find clicked chip."""
    if session_contents is not None:
        df = pd.DataFrame(session_contents["signatures_data"])
        all_sigs = [c for c in df.columns if c != "Type"]
    elif selected_file and selected_file in data:
        all_sigs = data[selected_file]
    else:
        return dash.no_update
    if not n_clicks or selected_sigs is None:
        return dash.no_update
    filtered_sigs = all_sigs
    if search_value:
        search_lower = search_value.lower()
        filtered_sigs = [s for s in all_sigs if search_lower in s.lower()]
    
    clicked_idx = next((i for i, c in enumerate(n_clicks) if c), None)
    if clicked_idx is None or clicked_idx >= len(filtered_sigs):
        return dash.no_update
    
    sig = filtered_sigs[clicked_idx]
    new_sigs = list(selected_sigs)
    
    if sig in new_sigs:
        new_sigs.remove(sig)
    else:
        new_sigs.append(sig)
    
    return new_sigs


@app.callback(
    Output("signatures-dropdown-1", "value", allow_duplicate=True),
    Input("selected-signatures-store-1", "data"),
    prevent_initial_call=True
)
def sync_dropdown_with_store(selected_sigs):
    """Keep the hidden dropdown in sync with the chip selection"""
    return selected_sigs if selected_sigs else []


# Callback removed - tooltip-button element doesn't exist in layout
# @app.callback(
#     Output("submit-button", "color"),
#     Output("tooltip-button", "style"),
#     Input("signatures-dropdown-1", "value"),
#     Input("submit-button", "n_clicks"),
#     prevent_initial_call=True
# )
# def highlight_button_on_dropdown_change(dropdown_values, n_clicks):
#     if ctx.triggered_id == "signatures-dropdown-1":
#         return "danger", {"display": "block"}
#     elif ctx.triggered_id == "submit-button":
#         return "primary", {"display": "none"}
#     return dash.no_update, dash.no_update


@app.callback(
    [Output('heatmap-plot', 'figure', allow_duplicate=True),
     Output('heatmap-reprint-plot', 'figure', allow_duplicate=True)],
    [Input('distance-metric', 'value'),
     Input('clustering-method', 'value'),
     Input('epsilon', 'value')],
    prevent_initial_call=True
)
def clear_plots_on_parameter_change(distance_metric, clustering_method, epsilon):
    """Clear plots when parameters change to avoid showing outdated data"""
    empty_fig = go.Figure()
    empty_fig.update_layout(
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[{
            'text': 'Click "Reload heatmaps" to generate new plots',
            'xref': 'paper',
            'yref': 'paper',
            'x': 0.5,
            'y': 0.5,
            'showarrow': False,
            'font': {'size': 16, 'color': '#666'}
        }],
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return empty_fig, empty_fig