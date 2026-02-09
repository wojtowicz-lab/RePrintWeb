from utils.utils import parse_signatures, FILES, DEFAULT_SIGNATURES, calculate_rmse, calculate_cosine, calculate_kl_divergence, calculate_js_divergence, reprint
from utils.figpanel import create_vertical_dendrogram_with_query_labels_right
from dash import dcc, html, Input, Output, State, ctx, ALL
from main import app
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from pages.nav import navbar
import pandas as pd
import dash
import plotly.graph_objects as go

functions = {'rmse': calculate_rmse, 'cosine': calculate_cosine, 'js_divergence': calculate_js_divergence}

DEFAULT_LINKAGE_METHOD = 'complete'
linkage_methods = ['single', 'complete', 'average', 'weighted', 'centroid', 'median']
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
    "red": "#E11D48",               # Vibrant Red (Generate Plots)
    "text_primary": "#1F2937",      # Dark text
    "text_secondary": "#6B7280",    # Secondary text
    "border": "#E5E7EB",            # Light border
    "shadow": "0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04)",
    "shadow_md": "0 4px 12px rgba(0, 0, 0, 0.12), 0 2px 6px rgba(0, 0, 0, 0.06)",
}

# ============================================================================
# APPLICATION LAYOUT
# ============================================================================
page4_layout = html.Div([
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
                                                html.H5("Reference Base vs Query Signatures", style={"margin": 0, "fontWeight": "600"}),
                                            ]
                                        ),
                                    ),
                                    dmc.AccordionPanel(
                                        children=dmc.Grid(
                                        children=[
                                            # Reference Base Column
                                            dmc.GridCol(
                                                span=4,
                                                children=[
                                                    html.H6("1. Reference Base (_ref)", style={"fontWeight": "600", "marginBottom": "1rem"}),
                                                    html.P(
                                                        "The reference base is a collection of predefined mutational signatures that serve as a benchmark for comparison. Examples include COSMIC.",
                                                        style={"fontSize": "0.95rem", "color": COLORS["text_primary"], "marginBottom": "0.75rem"}
                                                    ),
                                                    html.P(
                                                        "Each column represents a known signature (e.g., SBS1, SBS2), each row a mutation type.",
                                                        style={"fontSize": "0.95rem", "color": COLORS["text_primary"], "marginBottom": "0.75rem"}
                                                    ),
                                                    html.P(
                                                        "In the analysis, reference columns are marked with a '_ref' suffix.",
                                                        style={"fontSize": "0.95rem", "color": COLORS["text_primary"]}
                                                    ),
                                                ]
                                            ),
                                            # Query Signatures Column
                                            dmc.GridCol(
                                                span=4,
                                                children=[
                                                    html.H6("2. Query Signatures (_query)", style={"fontWeight": "600", "marginBottom": "1rem"}),
                                                    html.P(
                                                        "Query signatures are your own mutational signatures that you upload to compare against the reference base.",
                                                        style={"fontSize": "0.95rem", "color": COLORS["text_primary"], "marginBottom": "0.75rem"}
                                                    ),
                                                    html.Ul([
                                                        html.Li("Evaluate similarity to known reference signatures", style={"fontSize": "0.9rem", "marginBottom": "0.5rem"}),
                                                        html.Li("Visualize clustering relationships", style={"fontSize": "0.9rem", "marginBottom": "0.5rem"}),
                                                        html.Li("Detect novel mutational patterns", style={"fontSize": "0.9rem"}),
                                                    ], style={"paddingLeft": "1.5rem"}),
                                                ]
                                            ),
                                            # Distance Metrics Column
                                            dmc.GridCol(
                                                span=4,
                                                children=[
                                                    html.H6("3. Distance Metrics", style={"fontWeight": "600", "marginBottom": "1rem"}),
                                                    html.Ul([
                                                        html.Li(
                                                            [html.Strong("Cosine: "), "Angular similarity between vectors"],
                                                            style={"fontSize": "0.9rem", "marginBottom": "0.5rem"}
                                                        ),
                                                        html.Li(
                                                            [html.Strong("RMSE: "), "Root mean square error"],
                                                            style={"fontSize": "0.9rem", "marginBottom": "0.5rem"}
                                                        ),
                                                        html.Li(
                                                            [html.Strong("JS Divergence: "), "Jensen-Shannon divergence"],
                                                            style={"fontSize": "0.9rem"}
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
                                id="toggle-button-4",
                                color="dark",
                                size="md",
                                style={"backgroundColor": COLORS["navy"]},
                                leftSection=DashIconify(icon="tabler:adjustments", width=18),
                            ),
                            dmc.Button(
                                "Generate plots",
                                id="reload-button",
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
                id="collapse-form-4",
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
                                                id='distance-metric-4',
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
                                                id='clustering-method-4',
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
                                                id="epsilon-4",
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
            
            # Reference and Query Signatures Section
            dmc.Grid([
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
                                dmc.Group(
                                    children=[
                                        DashIconify(icon="tabler:database", width=20, height=20, color=COLORS["primary_blue"]),
                                        dmc.Text("Reference Signatures", size="md", fw=600),
                                    ],
                                    gap="sm",
                                    style={"marginBottom": "1.5rem"}
                                ),
                                
                                # Active Reference File Card
                                dmc.Paper(
                                    children=[
                                        dmc.Group(
                                            children=[
                                                DashIconify(icon="tabler:file-text", width=20, height=20, color=COLORS["primary_blue"]),
                                                dmc.Stack(
                                                    children=[
                                                        dmc.Text("Active File", size="xs", c="dimmed"),
                                                        dmc.Text(id="active-file-display-4", size="sm", fw=700, style={"color": COLORS["text_primary"]}),
                                                    ],
                                                    gap=0,
                                                ),
                                            ],
                                            grow=True,
                                            gap="sm",
                                        ),
                                    ],
                                    p="sm",
                                    radius="md",
                                    style={"backgroundColor": "#F0F5FB", "border": f"1px solid {COLORS['border']}", "marginBottom": "1rem"},
                                ),
                                
                                dmc.Text("Change Reference File", size="sm", fw=600, style={"marginBottom": "0.5rem"}),
                                dcc.Dropdown(
                                    id='dropdown-4',
                                    options=dropdown_options,
                                    value=DEFAULT_SIGNATURES,
                                ),
                                
                                html.Div(style={"marginTop": "1.5rem"}),
                                
                                # Signature Selection with Search
                                dmc.Group(
                                    children=[
                                        dmc.Text("Select Signatures", size="sm", fw=600),
                                        dmc.Group(
                                            children=[
                                                dmc.Button("Add All", id="add-all-btn-4", size="xs", variant="light", color="blue"),
                                                dmc.Button("Clear All", id="clear-all-btn-4", size="xs", variant="light", color="gray"),
                                            ],
                                            gap="xs",
                                        ),
                                    ],
                                    justify="space-between",
                                    style={"marginBottom": "0.75rem"}
                                ),
                                
                                # Search bar
                                dmc.TextInput(
                                    id="signature-search-4",
                                    placeholder="Search signatures...",
                                    leftSection=DashIconify(icon="tabler:search", width=18),
                                    style={"marginBottom": "0.75rem"},
                                ),
                                
                                # Signature Chips
                                html.Div(
                                    id="signatures-chips-container-4",
                                    style={
                                        "display": "flex",
                                        "flexWrap": "wrap",
                                        "gap": "0.5rem",
                                        "padding": "0.75rem",
                                        "backgroundColor": "#F8FAFC",
                                        "borderRadius": "0.375rem",
                                        "border": f"1px solid {COLORS['border']}",
                                        "minHeight": "100px",
                                        "alignContent": "flex-start",
                                    }
                                ),
                                
                                # Store for selected signatures (use _ref suffix to match df columns)
                                dcc.Store(id="selected-signatures-store-4", data=[f"{k}_ref" for k in data[DEFAULT_SIGNATURES]]),
                                
                                # Hidden dropdown - kept in sync with chips, used by other callbacks
                                html.Div(
                                    dcc.Dropdown(
                                        id='signatures-dropdown-4',
                                        options=[{'label': f"{s}_ref", 'value': f"{s}_ref"} for s in data[DEFAULT_SIGNATURES]],
                                        multi=True,
                                        value=[f"{s}_ref" for s in data[DEFAULT_SIGNATURES]],
                                    ),
                                    style={"display": "none"}
                                ),
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
                                dmc.Group(
                                    children=[
                                        DashIconify(icon="tabler:upload-cloud", width=20, height=20, color="#F59E0B"),
                                        dmc.Text("Query Signatures", size="md", fw=600),
                                    ],
                                    gap="sm",
                                    style={"marginBottom": "1.5rem"}
                                ),
                                dmc.Text("Upload Your Experimental Signatures", size="sm", fw=600, style={"marginBottom": "1rem"}),
                                dmc.Card(
                                    style={
                                        "backgroundColor": "#FEF9E7",
                                        "border": f"2px dashed #F39C12",
                                        "borderRadius": "0.75rem",
                                        "padding": "2rem",
                                        "textAlign": "center",
                                        "cursor": "pointer",
                                        "marginBottom": "1rem",
                                    },
                                    children=[
                                        dcc.Upload(
                                            id='upload-data-4-signatures',
                                            children=html.Div([
                                                DashIconify(icon="tabler:cloud-upload", width=40, height=40, color="#F39C12", style={"marginBottom": "0.75rem"}),
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
                                html.Div(id='info_uploader-4'),
                            ]
                        ),
                    ]
                ),
            ], gutter="md", grow=True, style={"marginBottom": "2.5rem"}),
            
            dcc.Interval(id='initial-load', interval=1000, n_intervals=0, max_intervals=1),
            dcc.Store(id='session-4-signatures', storage_type='session', data=None),
            
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
            
            # Dendrogram Visualization Section
            dmc.Grid([
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
                                html.H5("Signatures Dendrogram", style={"fontWeight": "600", "marginBottom": "1rem"}),
                                dcc.Loading(
                                    id="loading-heatmap-4",
                                    type="default",
                                    children=dcc.Graph(
                                        id='heatmap-plot-4',
                                        style={'height': '600px', 'minHeight': '400px', 'maxWidth': '100%'},
                                        config={
                                            'displayModeBar': True,
                                            'displaylogo': False,
                                            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                                            'modeBarButtonsToAdd': ['toImage'],
                                            'toImageButtonOptions': {
                                                'format': 'png',
                                                'filename': 'signature_similarity_dendrogram',
                                                'height': 600,
                                                'width': 800,
                                                'scale': 2
                                            },
                                            'responsive': True,
                                            'scrollZoom': True,
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
                                html.H5("RePrints Dendrogram", style={"fontWeight": "600", "marginBottom": "1rem"}),
                                dcc.Loading(
                                    id="loading-reprint-4",
                                    type="default",
                                    children=dcc.Graph(
                                        id='heatmap-reprint-plot-4',
                                        style={'height': '600px', 'minHeight': '400px', 'maxWidth': '100%'},
                                        config={
                                            'displayModeBar': True,
                                            'displaylogo': False,
                                            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                                            'modeBarButtonsToAdd': ['toImage'],
                                            'toImageButtonOptions': {
                                                'format': 'png',
                                                'filename': 'reprint_similarity_dendrogram',
                                                'height': 600,
                                                'width': 800,
                                                'scale': 2
                                            },
                                            'responsive': True,
                                            'scrollZoom': True,
                                        }
                                    )
                                )
                            ]
                        ),
                    ]
                ),
            ], gutter="md", grow=True, style={"marginBottom": "2.5rem"}),
            
            dcc.Location(id='url-page4', refresh=False),
        ]
    ),
])


# ============================================================================
# New Callbacks for Enhanced Signature Selection UI for Page4
# ============================================================================

@app.callback(
    Output("active-file-display-4", "children"),
    Input("dropdown-4", "value")
)
def update_active_file_display_4(selected_file):
    """Update the active file display"""
    if selected_file and selected_file in data:
        return selected_file
    return "None"


@app.callback(
    [Output("signatures-chips-container-4", "children"),
     Output("selected-signatures-store-4", "data")],
    [Input("dropdown-4", "value"),
     Input("signature-search-4", "value"),
     Input("add-all-btn-4", "n_clicks"),
     Input("clear-all-btn-4", "n_clicks"),
     Input("selected-signatures-store-4", "data")],
    prevent_initial_call=False
)
def update_signature_chips_4(selected_file, search_value, add_clicks, clear_clicks, selected_sigs):
    """Generate signature chips based on file and search/filter. Uses _ref suffix to match df columns."""
    if not selected_file or selected_file not in data:
        return [], []
    
    # Get all reference signatures with _ref suffix (matches df_ref column names)
    base_sigs = data[selected_file]
    all_sigs = [f"{s}_ref" for s in base_sigs]
    
    # Initialize selected_sigs if None
    if selected_sigs is None:
        selected_sigs = all_sigs.copy()
    
    # Handle "Add All" button
    if add_clicks and ctx.triggered_id == "add-all-btn-4":
        selected_sigs = all_sigs.copy()
    
    # Handle "Clear All" button
    if clear_clicks and ctx.triggered_id == "clear-all-btn-4":
        selected_sigs = []
    
    # Filter by search value (search in base names for UX)
    filtered_sigs = all_sigs
    if search_value:
        search_lower = search_value.lower()
        filtered_sigs = [s for s in all_sigs if search_lower in s.lower()]
    
    # Create chips (display base name without _ref for readability)
    chips = []
    for sig in filtered_sigs:
        is_selected = sig in selected_sigs
        display_name = sig.replace("_ref", "").replace("_query", "")
        chip = dmc.Button(
            display_name,
            id={"type": "sig-chip-4", "index": sig},
            color="blue" if is_selected else "gray",
            variant="filled" if is_selected else "light",
            size="xs",
            style={"cursor": "pointer", "fontSize": "0.85rem", "fontWeight": "500", "padding": "0.2rem 0.6rem"},
            n_clicks=0,
        )
        chips.append(chip)
    
    return chips, selected_sigs


@app.callback(
    Output("selected-signatures-store-4", "data", allow_duplicate=True),
    Input({"type": "sig-chip-4", "index": ALL}, "n_clicks"),
    [State("selected-signatures-store-4", "data"),
     State("dropdown-4", "value"),
     State("signature-search-4", "value")],
    prevent_initial_call=True
)
def toggle_signature_chip_4(n_clicks, selected_sigs, selected_file, search_value):
    """Handle individual chip clicks to toggle selection. Use n_clicks index to find clicked chip."""
    if not n_clicks or selected_sigs is None or not selected_file or selected_file not in data:
        return dash.no_update
    
    base_sigs = data[selected_file]
    all_sigs = [f"{s}_ref" for s in base_sigs]
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
    Output("signatures-dropdown-4", "value", allow_duplicate=True),
    Input("selected-signatures-store-4", "data"),
    prevent_initial_call=True
)
def sync_dropdown_with_store_4(selected_sigs):
    """Keep the hidden dropdown in sync with the chip selection"""
    return selected_sigs if selected_sigs else []


@app.callback(
    [Output('heatmap-plot-4', 'figure'),
     Output('heatmap-reprint-plot-4', 'figure')],
    [Input('initial-load', 'n_intervals'),
     Input('dropdown-4', 'value'),
     Input('reload-button', 'n_clicks')],
    [State('signatures-dropdown-4', 'value'),
     State('session-4-signatures', 'data'),
     State('distance-metric-4', 'value'),
     State('clustering-method-4', 'value'),
     State('epsilon-4', 'value')]
)
def update_graph(init_load, selected_file, n_clicks, selected_signatures, signatures, distance_metric, clustering_method, epsilon):
    ctx = dash.callback_context
    if not ctx.triggered:
        trigger_id = 'initial-load'
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if trigger_id == 'initial-load' or trigger_id == 'reload-button':
            if not selected_signatures or not selected_file:
                print("No signatures or file selected")
                return {}, {}
            
            print(f"Processing file: {selected_file}")
            print(f"Selected signatures: {selected_signatures}")
            print(f"Uploaded signatures: {signatures}")
            
            # Always load _ref from selected file
            df_ref = pd.read_csv(f"data/signatures/{selected_file}", sep='\t', index_col=0)
            df_ref.columns = [f"{c}_ref" for c in df_ref.columns]
            print(f"Loaded reference data shape: {df_ref.shape}")
            
            # If uploaded, merge _query columns
            if signatures is not None:
                if isinstance(signatures, list):
                    df_query = pd.DataFrame(signatures[0]['signatures_data'])
                else:
                    df_query = pd.DataFrame(signatures['signatures_data'])
                print(f"Loaded query data shape: {df_query.shape}")
                
                if 'Type' in df_query.columns:
                    df_query.set_index('Type', inplace=True)
                # Merge on index (Type)
                df_all = df_ref.join(df_query, how='inner')
                print(f"Merged data shape: {df_all.shape}")
            else:
                df_all = df_ref
                print("No uploaded signatures, using only reference data")
            
            df_all = df_all[[col for col in selected_signatures if col in df_all.columns]]
            print(f"Final data shape: {df_all.shape}")
            print(f"Final data columns: {df_all.columns.tolist()}")
            print(f"Final data index: {df_all.index.tolist()[:5]}")  # First 5 rows
            
            if df_all.empty:
                print("Warning: Final dataframe is empty!")
                return {}, {}
            
            try:
                df_reprint = reprint(df_all, epsilon=epsilon)[df_all.columns]
                print(f"RePrint data shape: {df_reprint.shape}")
            except Exception as e:
                print(f"Error in reprint function: {str(e)}")
                df_reprint = df_all  # Fallback to original data
            
            return (
                create_vertical_dendrogram_with_query_labels_right(df_all, calc_func=functions[distance_metric], method=clustering_method, text="Signatures"),
                create_vertical_dendrogram_with_query_labels_right(df_reprint, calc_func=functions[distance_metric], method=clustering_method, text="RePrints")
            )
        else:
            return {}, {}
    except Exception as e:
        print(f"Error in update_graph: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}, {}


@app.callback(
    Output('session-4-signatures', 'data'),
    Input('upload-data-4-signatures', 'contents'),
    State('upload-data-4-signatures', 'filename'),
    State('dropdown-4', 'value')
)
def update_output_signatures(contents, filename, selected_file):
    if contents is None:
        return dash.no_update

    try:
        # Only parse uploaded file as _query
        df_query = parse_signatures(contents, filename)
        if 'Type' in df_query.columns:
            df_query.set_index('Type', inplace=True)
        df_query = df_query.rename(columns={col: f"{col}_query" for col in df_query.columns})
        df_query.reset_index(inplace=True)

        return [{
            'signatures_data': df_query.to_dict('records'),
            'filename': filename,
            'info': f'Uploaded file {filename} as _query signatures'
        }]
    except Exception as e:
        print(f"Error in update_output_signatures: {str(e)}")
        # Return error info for debugging
        return [{
            'signatures_data': [],
            'filename': filename,
            'info': f'Error uploading file: {str(e)}'
        }]


@app.callback(
    [Output('signatures-dropdown-4', 'options'),
     Output('signatures-dropdown-4', 'value'),
     Output('dropdown-4', 'style'),
     Output('info_uploader-4', 'children')],
    [Input('dropdown-4', 'value'),
     Input('session-4-signatures', 'data')],
)
def set_options(selected_category, contents):
    try:
        print(f"set_options called with category: {selected_category}")
        print(f"Contents: {contents}")
        
        base_signatures = data[selected_category]
        print(f"Base signatures: {base_signatures[:5]}...")  # First 5
        
        # Always load _ref from selected file, _query from upload if present
        ref_cols = [f"{s}_ref" for s in base_signatures]
        query_cols = []
        info = 'Not Uploaded'
        
        if contents is not None:
            if isinstance(contents, list):
                content = contents[0]
            else:
                content = contents
            
            print(f"Processing content: {content}")
            
            df = pd.DataFrame(content['signatures_data'])
            print(f"DataFrame shape: {df.shape}")
            print(f"DataFrame columns: {df.columns.tolist()}")
            
            if 'Type' in df.columns:
                df.set_index('Type', inplace=True)
                print(f"After setting index: {df.shape}")
            
            all_columns = df.columns.tolist()
            query_cols = sorted([col for col in all_columns if col.endswith('_query')])
            print(f"Query columns found: {query_cols}")
            info = content.get('info', 'Uploaded file as _query signatures')
        
        combined = ref_cols + query_cols
        print(f"Combined columns: {combined[:10]}...")  # First 10
        
        return (
            [{'label': sig, 'value': sig} for sig in combined],
            combined,
            {'display': 'block'},
            info
        )
    except Exception as e:
        print(f"Error in set_options: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return fallback values
        base_signatures = data.get(selected_category, [])
        ref_cols = [f"{s}_ref" for s in base_signatures]
        return (
            [{'label': sig, 'value': sig} for sig in ref_cols],
            ref_cols,
            {'display': 'block'},
            f'Error: {str(e)}'
        )

@app.callback(
    Output("collapse-form-4", "opened"),
    [Input("toggle-button-4", "n_clicks")],
    [State("collapse-form-4", "opened")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    [Output('heatmap-plot-4', 'figure', allow_duplicate=True),
     Output('heatmap-reprint-plot-4', 'figure', allow_duplicate=True)],
    [Input('distance-metric-4', 'value'),
     Input('clustering-method-4', 'value'),
     Input('epsilon-4', 'value')],
    prevent_initial_call=True
)
def clear_plots_on_parameter_change(distance_metric, clustering_method, epsilon):
    """Clear plots when parameters change to avoid showing outdated data"""
    empty_fig = go.Figure()
    empty_fig.update_layout(
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[{
            'text': 'Click "Generate plots" to create new dendrograms',
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


@app.callback(
    [Output('heatmap-plot-4', 'figure', allow_duplicate=True),
     Output('heatmap-reprint-plot-4', 'figure', allow_duplicate=True)],
    Input('signatures-dropdown-4', 'value'),
    prevent_initial_call=True
)
def clear_plots_on_signature_change(selected_signatures):
    """Clear plots when signature selection changes to avoid showing outdated data"""
    empty_fig = go.Figure()
    empty_fig.update_layout(
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[{
            'text': 'Click "Generate plots" to create new dendrograms',
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


@app.callback(
    [Output('heatmap-plot-4', 'figure', allow_duplicate=True),
     Output('heatmap-reprint-plot-4', 'figure', allow_duplicate=True)],
    Input('dropdown-4', 'value'),
    prevent_initial_call=True
)
def clear_plots_on_file_change(selected_file):
    """Clear plots when reference file changes to avoid showing outdated data"""
    empty_fig = go.Figure()
    empty_fig.update_layout(
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[{
            'text': 'Click "Generate plots" to create new dendrograms',
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


@app.callback(
    [Output('heatmap-plot-4', 'figure', allow_duplicate=True),
     Output('heatmap-reprint-plot-4', 'figure', allow_duplicate=True)],
    Input('session-4-signatures', 'data'),
    prevent_initial_call=True
)
def clear_plots_on_upload(uploaded_data):
    """Clear plots when new signatures are uploaded to avoid showing outdated data"""
    if uploaded_data is not None:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            xaxis={'visible': False},
            yaxis={'visible': False},
            annotations=[{
                'text': 'Click "Generate plots" to create new dendrograms',
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
    return dash.no_update, dash.no_update