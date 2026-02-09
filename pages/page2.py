from utils.figpanel import create_main_dashboard, create_reprint_footprint_figure
from dash import dcc, html
from main import app
from dash import Input, Output, State, ctx, ALL
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from pages.nav import navbar
import pandas as pd
from utils.utils import FILES, DEFAULT_SIGNATURES, reprint, parse_signatures
import dash
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
page2_layout = html.Div([
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
                                                            html.Li("Choose a reference signature file from the first dropdown (e.g., COSMIC).", style={"marginBottom": "0.75rem"}),
                                                            html.Li("Optionally upload your own mutational signatures (.txt format).", style={"marginBottom": "0.75rem"}),
                                                            html.Li("Select the signatures to visualize from the second dropdown.", style={"marginBottom": "0.75rem"}),
                                                            html.Li([
                                                                html.Strong("Click "), "the ",
                                                                html.Strong("Generate Plots"),
                                                                " button to refresh visualizations."
                                                            ]),
                                                        ],
                                                        style={"fontSize": "0.95rem", "color": COLORS["text_primary"]}
                                                    ),
                                                ]
                                            ),
                                            # Plot Display Column
                                            dmc.GridCol(
                                                span=4,
                                                children=[
                                                    html.H6("2. Plot Display", style={"fontWeight": "600", "marginBottom": "1rem"}),
                                                    html.Ul([
                                                        html.Li(
                                                            [html.Strong("Left: "), "Original signature (mutation frequencies)"],
                                                            style={"marginBottom": "0.75rem", "fontSize": "0.95rem", "color": COLORS["text_primary"]}
                                                        ),
                                                        html.Li(
                                                            [html.Strong("Right: "), "RePrint-transformed representation (functional footprint)"],
                                                            style={"marginBottom": "0.75rem", "fontSize": "0.95rem", "color": COLORS["text_primary"]}
                                                        ),
                                                        html.Li(
                                                            "Use navigation buttons to browse through paginated results (5 plots per page)",
                                                            style={"fontSize": "0.95rem", "color": COLORS["text_primary"]}
                                                        ),
                                                    ], style={"paddingLeft": "1.5rem"}),
                                                ]
                                            ),
                                            # Advanced Options Column
                                            dmc.GridCol(
                                                span=4,
                                                children=[
                                                    html.H6("3. Advanced Options", style={"fontWeight": "600", "marginBottom": "1rem"}),
                                                    html.Ul([
                                                        html.Li(
                                                            "Adjust the epsilon (ε) parameter to reduce noise",
                                                            style={"marginBottom": "0.75rem", "fontSize": "0.95rem", "color": COLORS["text_primary"]}
                                                        ),
                                                        html.Li(
                                                            "Downloads for RePrint and signature data",
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
                                id="toggle-button-2",
                                color="dark",
                                size="md",
                                style={"backgroundColor": COLORS["navy"]},
                                leftSection=DashIconify(icon="tabler:adjustments", width=18),
                            ),
                            dmc.Button(
                                "Download Reprints",
                                id="btn_csv-2",
                                color="teal",
                                size="md",
                                style={"backgroundColor": COLORS["teal"]},
                                leftSection=DashIconify(icon="tabler:download", width=18),
                            ),
                            dmc.Button(
                                "Download Signatures",
                                id="btn_csv-signatures-2",
                                color="gray",
                                size="md",
                                leftSection=DashIconify(icon="tabler:download", width=18),
                            ),
                            dmc.Button(
                                "Generate Plots",
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
                id="collapse-form-2",
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
                                        span=12,
                                        children=[
                                            dmc.Text("Epsilon (pseudo-count)", size="sm", fw=600, style={"marginBottom": "0.5rem"}),
                                            dmc.NumberInput(
                                                id="epsilon-2",
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
                                                    dmc.Text(id="active-file-display-2", size="md", fw=700, style={"color": COLORS["text_primary"]}),
                                                    dmc.Badge(id="signature-count-2", size="sm", color="blue", variant="light"),
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
                                id='dropdown-2',
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
                                            dmc.Button("Add All", id="add-all-btn-2", size="xs", variant="light", color="blue"),
                                            dmc.Button("Clear All", id="clear-all-btn-2", size="xs", variant="light", color="gray"),
                                        ],
                                        gap="xs",
                                    ),
                                ],
                                justify="space-between",
                            ),
                            
                            # Search bar
                            dmc.TextInput(
                                id="signature-search-2",
                                placeholder="Search signatures...",
                                leftSection=DashIconify(icon="tabler:search", width=18),
                                style={"marginBottom": "1rem"},
                            ),
                            
                            # Signature Chips/Badges
                            html.Div(
                                id="signatures-chips-container-2",
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
                    dcc.Store(id="selected-signatures-store-2", data=[k for k in data[DEFAULT_SIGNATURES]]),
                    
                    # Hidden dropdown - kept in sync with chips, used by other callbacks
                    html.Div(
                        dcc.Dropdown(
                            id='signatures-dropdown-2',
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
                        id='upload-data-2-signatures',
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
            
            html.Div(id='upload-error-message-2'),
            html.Div(id='info_uploader-2'),
            dcc.Store(id='session-2-signatures', storage_type='session', data=None),
            dcc.Location(id='url-page2', refresh=False),
            dcc.Interval(id='initial-load', interval=1000, n_intervals=0, max_intervals=1),
            
            # Plots Container with Loading
            dcc.Loading(
                id="loading-graphs",
                type="default",
                children=html.Div(id='plots-container-2')
            ),
            
            dcc.Download(id="download-dataframe-csv-2"),
            dcc.Download(id="download-dataframe-csv-signatures-2"),
            dcc.Store(id='plots-page-store', data=0),
            html.Div(id='plots-navigation', style={"marginTop": "2rem", "marginBottom": "2rem"}),
        ]
    ),
])

@app.callback(
    Output('plots-page-store', 'data'),
    Input('prev-page-btn', 'n_clicks'),
    Input('next-page-btn', 'n_clicks'),
    State('plots-page-store', 'data'),
    prevent_initial_call=True
)
def update_page(prev_clicks, next_clicks, current_page):
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger == 'prev-page-btn' and current_page > 0:
        return current_page - 1
    elif trigger == 'next-page-btn':
        return current_page + 1
    return current_page

@app.callback(
    Output('plots-container-2', 'children'),
    Output('plots-navigation', 'children'),
    [Input('initial-load', 'n_intervals'),
     Input('dropdown-2', 'value'),
     Input('reload-button', 'n_clicks'),
     Input('plots-page-store', 'data')],
    [State('signatures-dropdown-2', 'value'),
     State('epsilon-2', 'value'),
     State('session-2-signatures', 'data')]
)
def update_graph(init_load, selected_file, n_clicks, current_page, selected_signatures, epsilon, signatures):
    ctx = dash.callback_context
    if not ctx.triggered:
        trigger_id = 'initial-load'
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id in ['initial-load', 'reload-button', 'plots-page-store']:
        if not selected_signatures or not selected_file:
            return [], None

        if signatures is not None:
            df_signatures = pd.DataFrame(signatures['signatures_data'])
            df_signatures.index = df_signatures['Type']
            df_signatures = df_signatures.drop(columns='Type')
            df_reprint = reprint(df_signatures, epsilon=epsilon)[selected_signatures]
        else:
            df_signatures = pd.read_csv(f"data/signatures/{selected_file}", sep='\t', index_col=0)[selected_signatures]
            df_reprint = pd.read_csv(f"data/cosmic_reprints/{selected_file}.reprint", sep='\t', index_col=0)[selected_signatures]

        per_page = 5
        total_pages = (len(selected_signatures) + per_page - 1) // per_page
        current_page = min(current_page, total_pages - 1)
        start = current_page * per_page
        end = start + per_page
        visible_signatures = selected_signatures[start:end]

        plots = []
        for signature in visible_signatures:
            plots.append(
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
                                    html.H6(f"Original {signature}", style={"fontWeight": "600", "marginBottom": "1rem"}),
                                    dcc.Graph(
                                        id=f'graph-original-{signature.replace(" ", "_").replace("-", "_")}',
                                        figure=create_main_dashboard(
                                            df_signatures,
                                            signature=signature,
                                            title=f'{signature}',
                                            yaxis_title='Frequencies'
                                        ),
                                        config={
                                            'displayModeBar': True,
                                            'displaylogo': False,
                                            'modeBarButtonsToAdd': [
                                                'toImage'
                                            ],
                                            'toImageButtonOptions': {
                                                'format': 'png',
                                                'filename': f'{signature}_plot',
                                                'height': 520,
                                                'width': 1000,
                                                'scale': 2
                                            }
                                        }
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
                                    html.H6(f"RePrint {signature}", style={"fontWeight": "600", "marginBottom": "1rem"}),
                                    dcc.Graph(
                                        id=f'graph-reprint-{signature.replace(" ", "_").replace("-", "_")}',
                                        figure=create_reprint_footprint_figure(
                                            df_reprint,
                                            signature=signature,
                                            title=f'RePrint_{signature}',
                                        ),
                                        config={
                                            'displayModeBar': True,
                                            'displaylogo': False,
                                            'modeBarButtonsToAdd': [
                                                'toImage'
                                            ],
                                            'toImageButtonOptions': {
                                                'format': 'png',
                                                'filename': f'Reprint_{signature}_plot',
                                                'height': 520,
                                                'width': 1000,
                                                'scale': 2
                                            }
                                        }
                                    ),
                                ]
                            ),
                        ]
                    ),
                ], gutter="md", grow=True, style={"marginBottom": "2rem"})
            )

        navigation = dmc.Group(
            children=[
                dmc.Button("Previous", id="prev-page-btn", disabled=(current_page == 0), color="gray", variant="default"),
                dmc.Text(f"Page {current_page + 1} of {total_pages}", size="md", fw=500),
                dmc.Button("Next", id="next-page-btn", disabled=(current_page >= total_pages - 1), color="gray", variant="default")
            ],
            justify="center",
            align="center",
            gap="md"
        )

        return plots, navigation

    return [], None

@app.callback(
    Output('session-2-signatures', 'data'),
    Input('upload-data-2-signatures', 'contents'),
    State('upload-data-2-signatures', 'filename'),
    prevent_initial_call=True
)
def update_session_2_data(contents, filename):
    if contents is not None:
        try:
            df_signatures = parse_signatures(contents, filename)
            return {
                'signatures_data': df_signatures.to_dict('records'),
                'filename': filename,
                'info': "Signatures uploaded successfully"
            }
        except Exception:
            return dash.no_update
    return dash.no_update

@app.callback(
    Output('upload-error-message-2', 'children'),
    Input('upload-data-2-signatures', 'contents'),
    State('upload-data-2-signatures', 'filename'),
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
    [Output('signatures-dropdown-2', 'options'),
     Output('signatures-dropdown-2', 'value'),
     Output('dropdown-2', 'style'),
     Output('info_uploader-2', 'children')
     ],
    [Input('dropdown-2', 'value'),
     Input('session-2-signatures', 'data')]
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


# ============================================================================
# New Callbacks for Enhanced Signature Selection UI
# ============================================================================

@app.callback(
    [Output("active-file-display-2", "children"),
     Output("signature-count-2", "children")],
    [Input("dropdown-2", "value"),
     Input("session-2-signatures", "data")]
)
def update_active_file_display_2(selected_file, session_contents):
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
    [Output("signatures-chips-container-2", "children"),
     Output("selected-signatures-store-2", "data")],
    [Input("dropdown-2", "value"),
     Input("session-2-signatures", "data"),
     Input("signature-search-2", "value"),
     Input("add-all-btn-2", "n_clicks"),
     Input("clear-all-btn-2", "n_clicks"),
     Input("selected-signatures-store-2", "data")],
    prevent_initial_call=False
)
def update_signature_chips_2(selected_file, session_contents, search_value, add_clicks, clear_clicks, selected_sigs):
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
    if add_clicks and ctx.triggered_id == "add-all-btn-2":
        selected_sigs = all_sigs.copy()
    
    # Handle "Clear All" button
    if clear_clicks and ctx.triggered_id == "clear-all-btn-2":
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
            id={"type": "sig-chip-2", "index": sig},
            color="blue" if is_selected else "gray",
            variant="filled" if is_selected else "light",
            size="xs",
            style={"cursor": "pointer", "fontSize": "0.9rem", "fontWeight": "500", "padding": "0.25rem 0.75rem"},
            n_clicks=0,
        )
        chips.append(chip)
    
    return chips, selected_sigs


@app.callback(
    Output("selected-signatures-store-2", "data", allow_duplicate=True),
    Input({"type": "sig-chip-2", "index": ALL}, "n_clicks"),
    [State("selected-signatures-store-2", "data"),
     State("dropdown-2", "value"),
     State("session-2-signatures", "data"),
     State("signature-search-2", "value")],
    prevent_initial_call=True
)
def toggle_signature_chip_2(n_clicks, selected_sigs, selected_file, session_contents, search_value):
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
    Output("signatures-dropdown-2", "value", allow_duplicate=True),
    Input("selected-signatures-store-2", "data"),
    prevent_initial_call=True
)
def sync_dropdown_with_store_2(selected_sigs):
    """Keep the hidden dropdown in sync with the chip selection"""
    return selected_sigs if selected_sigs else []


@app.callback(
    Output("download-dataframe-csv-2", "data"),
    Input("btn_csv-2", "n_clicks"),
    [State('signatures-dropdown-2', 'value'),
     State('dropdown-2', 'value'),
     State('epsilon-2', 'value'),
     State('session-2-signatures', 'data')],
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

@app.callback(
    Output("collapse-form-2", "opened"),
    [Input("toggle-button-2", "n_clicks")],
    [State("collapse-form-2", "opened")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("download-dataframe-csv-signatures-2", "data"),
    Input("btn_csv-signatures-2", "n_clicks"),
    [
        State('signatures-dropdown-2', 'value'),
        State('dropdown-2', 'value'),
        State('session-2-signatures', 'data')
    ],
    prevent_initial_call=True
)
def download_signatures_only_2(n_clicks, selected_signatures, selected_file, contents):
    if contents is not None:
        df_signatures = pd.DataFrame(contents['signatures_data'])
        df_signatures.index = df_signatures['Type']
        df_signatures = df_signatures.drop(columns='Type')[selected_signatures]
    else:
        df_signatures = pd.read_csv(f"data/signatures/{selected_file}", sep='\t', index_col=0)[selected_signatures]

    return dcc.send_data_frame(df_signatures.to_csv, filename="signatures.csv")



@app.callback(
    Output('plots-container-2', 'children', allow_duplicate=True),
    Input('epsilon-2', 'value'),
    prevent_initial_call=True
)
def clear_plots_on_parameter_change(epsilon):
    """Clear plots when epsilon parameter changes to avoid showing outdated data"""
    return html.Div(
        style={"textAlign": "center", "paddingTop": "3rem", "paddingBottom": "3rem"},
        children=[
            dmc.Alert([
                html.H5("Parameters Changed", style={"marginBottom": "0.5rem"}),
                html.P("The epsilon parameter has been modified. Click 'Generate Plots' to refresh the visualizations with the new settings."),
                html.P("This ensures that the displayed data matches your current parameter configuration.")
            ], icon=DashIconify(icon="tabler:info-circle", width=18), color="blue", title="Info")
        ]
    )


@app.callback(
    Output('plots-container-2', 'children', allow_duplicate=True),
    Input('signatures-dropdown-2', 'value'),
    prevent_initial_call=True
)
def clear_plots_on_signature_change(selected_signatures):
    """Clear plots when signature selection changes to avoid showing outdated data"""
    return html.Div(
        style={"textAlign": "center", "paddingTop": "3rem", "paddingBottom": "3rem"},
        children=[
            dmc.Alert([
                html.H5("Signature Selection Changed", style={"marginBottom": "0.5rem"}),
                html.P("The signature selection has been modified. Click 'Generate Plots' to refresh the visualizations with the new selection."),
                html.P("This ensures that the displayed data matches your current signature selection.")
            ], icon=DashIconify(icon="tabler:alert-circle", width=18), color="yellow", title="Warning")
        ]
    )


@app.callback(
    Output('plots-container-2', 'children', allow_duplicate=True),
    Input('dropdown-2', 'value'),
    prevent_initial_call=True
)
def clear_plots_on_file_change(selected_file):
    """Clear plots when reference file changes to avoid showing outdated data"""
    return html.Div(
        style={"textAlign": "center", "paddingTop": "3rem", "paddingBottom": "3rem"},
        children=[
            dmc.Alert([
                html.H5("Reference File Changed", style={"marginBottom": "0.5rem"}),
                html.P("The reference signature file has been changed. Click 'Generate Plots' to refresh the visualizations with the new reference data."),
                html.P("This ensures that the displayed data matches your current reference file selection.")
            ], icon=DashIconify(icon="tabler:info-circle", width=18), color="cyan", title="Info")
        ]
    )


@app.callback(
    Output('plots-container-2', 'children', allow_duplicate=True),
    Input('session-2-signatures', 'data'),
    prevent_initial_call=True
)
def clear_plots_on_upload(uploaded_data):
    """Clear plots when new signatures are uploaded to avoid showing outdated data"""
    if uploaded_data is not None:
        return html.Div(
            style={"textAlign": "center", "paddingTop": "3rem", "paddingBottom": "3rem"},
            children=[
                dmc.Alert([
                    html.H5("New Signatures Uploaded", style={"marginBottom": "0.5rem"}),
                    html.P("New signature data has been uploaded. Click 'Generate Plots' to refresh the visualizations with the new data."),
                    html.P("This ensures that the displayed data matches your uploaded signature file.")
                ], icon=DashIconify(icon="tabler:check-circle", width=18), color="green", title="Success")
            ]
        )
    return dash.no_update