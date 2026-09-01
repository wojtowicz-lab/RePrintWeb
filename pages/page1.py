from utils.figpanel import create_heatmap_with_custom_sim, MIN_FIGURE_SIZE, GNBU_9, ORRD_9
from utils.utils import FILES, DEFAULT_SIGNATURES, linkage_methods, DEFAULT_LINKAGE_METHOD, reprint, calculate_rmse, calculate_cosine, calculate_js_divergence
from utils.utils import (example_set_options, DEFAULT_EXAMPLE_SET, EXAMPLE_SIGNATURE_SETS,
                         LEGIBLE_SIGNATURE_LIMIT, PAPER_GOLD_STANDARD_GROUPS, PAPER_FIGURE_PRESET)
from main import app
from dash import dcc, html, Input, Output, State, ctx
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from pages.nav import navbar
import pandas as pd
import plotly.graph_objects as go




data = {}
for file in FILES:
    data[file] = pd.read_csv(f'data/signatures/{file}', sep='\t').columns[1:].to_list()

dropdown_options = [{'label': file, 'value': file} for file in FILES]

# Example datasets offered by the loader below. Each entry carries its own
# signature count and description so the picker can show what you are about to
# load before you load it.
EXAMPLE_SETS = example_set_options()
EXAMPLE_SET_OPTIONS = [{'label': o['label'], 'value': o['value']} for o in EXAMPLE_SETS]
EXAMPLE_SET_BLURBS = {o['value']: o['blurb'] for o in EXAMPLE_SETS}
EXAMPLE_SET_COUNTS = {o['value']: o['count'] for o in EXAMPLE_SETS}


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
                                                            html.Li("Or load a published dataset with the dataset picker, or upload your own query signatures using the drag-and-drop box — upload multiple files at once to merge them (aligned by mutation Type) before clustering.", style={"marginBottom": "0.75rem"}),
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
                                                            [html.Strong("RMSE: "), "Root mean square error between the two probability vectors - the metric the RePrint paper reports"],
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
                    
                    # Select Signatures – multi-select dropdown (stable mechanism)
                    dmc.Stack(
                        children=[
                            dmc.Text("Select Signatures", size="sm", fw=600),
                            dcc.Dropdown(
                                id='signatures-dropdown-1',
                                options=[{'label': k, 'value': k} for k in data[DEFAULT_SIGNATURES]],
                                multi=True,
                                value=[k for k in data[DEFAULT_SIGNATURES]],
                                placeholder="Choose signatures...",
                                style={"minWidth": "200px"},
                            ),
                            html.Div(id='signature-legibility-warning'),
                        ],
                        gap="xs",
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
                                        "The uploaded file should be a tab-separated file (.txt/.tsv) or CSV containing mutation types and corresponding mutation signatures.",
                                        style={"fontSize": "0.95rem", "marginBottom": "0.75rem"}
                                    ),
                                    html.P(
                                        "You can upload several files at once (e.g. COSMIC, Kucab2019, Zou2018). They will be merged into a single dataset aligned by the Type column; if two files share a signature name, the column is prefixed with its source filename to avoid ambiguity.",
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
                            html.P("Drag and drop your signature file(s) here, or click to select", style={"fontSize": "1rem", "fontWeight": "500"}),
                            html.P("Accepted formats: .txt/.tsv (tab-separated) or .csv (e.g. organ signatures). Select multiple files to merge them.", style={"fontSize": "0.85rem", "color": COLORS["text_secondary"]})
                        ]),
                        multiple=True,
                        style={
                            "width": "100%",
                            "cursor": "pointer",
                        }
                    ),
                    html.Div(style={"marginTop": "1.25rem"}),
                    dmc.Divider(label="or", labelPosition="center"),
                    html.Div(style={"marginTop": "1.25rem"}),
                    html.Div(
                        style={
                            "maxWidth": "560px",
                            "margin": "0 auto",
                            "textAlign": "left",
                        },
                        children=[
                            dmc.Group(
                                gap=8,
                                align="center",
                                justify="center",
                                style={"marginBottom": "0.75rem"},
                                children=[
                                    DashIconify(icon="tabler:flask", width=18, color=COLORS["primary_blue"]),
                                    dmc.Text("Load a published dataset", size="sm", fw=600),
                                ],
                            ),
                            dcc.Dropdown(
                                id="example-set-select",
                                options=EXAMPLE_SET_OPTIONS,
                                value=DEFAULT_EXAMPLE_SET,
                                clearable=False,
                                style={"textAlign": "left"},
                            ),
                            dmc.Text(
                                EXAMPLE_SET_BLURBS[DEFAULT_EXAMPLE_SET],
                                id="example-set-blurb",
                                size="xs",
                                c="dimmed",
                                style={"marginTop": "0.5rem", "minHeight": "2.5rem"},
                            ),
                            dmc.Button(
                                "Load dataset",
                                id="load-example-btn",
                                variant="outline",
                                color="blue",
                                size="md",
                                leftSection=DashIconify(icon="tabler:download", width=18),
                                style={"marginTop": "0.5rem", "width": "100%"},
                            ),
                            dmc.Text(
                                "Signature sets from the RePrint paper (data/signatures/paper/), "
                                "merged on mutation Type exactly like uploaded files.",
                                size="xs",
                                c="dimmed",
                                style={"marginTop": "0.5rem", "textAlign": "center"},
                            ),
                        ],
                    ),
                    dmc.Button(
                        "Clear Uploaded Signatures",
                        id="clear-upload-btn",
                        variant="subtle",
                        color="gray",
                        size="sm",
                        leftSection=DashIconify(icon="tabler:x", width=16),
                        style={"marginTop": "1rem", "display": "none"},
                    ),
                    dmc.Text(
                        "Switches back to the bundled reference file dropdown (e.g. COSMIC).",
                        size="xs",
                        c="dimmed",
                        id="clear-upload-hint",
                        style={"marginTop": "0.25rem", "display": "none"},
                    ),
                ]
            ),

            html.Div(id='upload-error-message-1'),
            html.Div(id='info_uploader'),
            dcc.Store(id='session-1-signatures', storage_type='session', data=None),
            dcc.Interval(id='initial-load-1', interval=1000, n_intervals=0, max_intervals=1),
            dcc.Store(id='auto-reload-armed', data=False),
            dcc.Store(id='reload-signal', data=0),
            
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
                                    dmc.GridCol(
                                        span=12,
                                        children=[
                                            dmc.Text("Cluster Granularity (dendrogram cut threshold)", size="sm", fw=600, style={"marginBottom": "0.5rem"}),
                                            dmc.Slider(
                                                id="cluster-threshold",
                                                value=0.7,
                                                min=0.1,
                                                max=0.9,
                                                step=0.05,
                                                marks=[
                                                    {"value": 0.1, "label": "More clusters"},
                                                    {"value": 0.9, "label": "Fewer clusters"},
                                                ],
                                                style={"width": "100%", "marginBottom": "1.5rem"}
                                            ),
                                            dmc.Text(
                                                "Cuts the dendrogram at this fraction of its tallest branch to group signatures into clusters on the heatmap. Lower it to split large clusters into smaller ones. Default: 0.7",
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
                                                id="paper-groups-switch",
                                                checked=False,
                                                label="Annotate the paper's gold-standard groups",
                                                size="sm",
                                            ),
                                            dmc.Text(
                                                "Colours the strip above the matrix by the reference group each signature "
                                                "is expected to fall into (the published figure's annotation) instead of "
                                                "by the clusters cut from this dendrogram. Only the 39 annotated "
                                                "signatures are coloured; everything else stays blank.",
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
            
            # Gold-standard group legend, filled in only while the paper's
            # annotation strip is switched on.
            html.Div(id='gold-standard-legend'),

            # Heatmaps Grid
            dmc.Grid(
                children=[
                    dmc.GridCol(
                        # Full width: the clustered heatmaps run 1200-2200px
                        # wide, so half-page columns can never fit them.
                        span=12,
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
                                        # The graph autosizes to fill this wrapper; its
                                        # style (set by the callback) clamps it between a
                                        # readability floor and a max size, and anything
                                        # below the floor scrolls here instead of clipping.
                                        children=html.Div(
                                            style={"overflowX": "auto"},
                                            children=dcc.Graph(
                                                id='heatmap-plot',
                                                responsive=True,
                                                style={"width": "100%", "height": "300px"},
                                                config={
                                                    'displayModeBar': True,
                                                    'displaylogo': False,
                                                    'modeBarButtonsToAdd': ['toImage'],
                                                    'toImageButtonOptions': {
                                                        'format': 'png',
                                                        'filename': 'signature_similarity_heatmap',
                                                        'scale': 2
                                                    }
                                                }
                                            )
                                        )
                                    )
                                ]
                            ),
                        ]
                    ),
                    dmc.GridCol(
                        span=12,
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
                                        children=html.Div(
                                            style={"overflowX": "auto"},
                                            children=dcc.Graph(
                                                id='heatmap-reprint-plot',
                                                responsive=True,
                                                style={"width": "100%", "height": "300px"},
                                                config={
                                                    'displayModeBar': True,
                                                    'displaylogo': False,
                                                    'modeBarButtonsToAdd': ['toImage'],
                                                    'toImageButtonOptions': {
                                                        'format': 'png',
                                                        'filename': 'reprint_similarity_heatmap',
                                                        'scale': 2
                                                    }
                                                }
                                            )
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

from utils.utils import parse_signatures, merge_uploaded_signatures, load_example_merged_signatures
import dash


def _as_lists(contents, filename):
    """dcc.Upload with multiple=True normally returns lists, but guard against
    a single value just in case."""
    if not isinstance(contents, list):
        return [contents], [filename]
    return contents, filename


def _merged_base_name(filenames):
    """Build a filesystem-friendly prefix from one or more uploaded filenames."""
    if not filenames:
        return "uploaded_signatures"
    if isinstance(filenames, str):
        filenames = [filenames]
    stems = [f.rsplit('.', 1)[0] if '.' in f else f for f in filenames]
    joined = "_".join(stems)
    return joined if len(joined) <= 60 else f"merged_{len(stems)}_files"


@app.callback(
    [Output('session-1-signatures', 'data')],
    [Input('upload-data-1-signatures', 'contents')],
    [State('upload-data-1-signatures', 'filename')]
)
def update_output_signatures(contents, filename):
    if contents is not None:
        contents_list, filenames_list = _as_lists(contents, filename)
        df_signatures, errors = merge_uploaded_signatures(contents_list, filenames_list)

        if df_signatures is None:
            return dash.no_update

        failed_names = {f for f, _ in errors}
        succeeded_names = [f for f in filenames_list if f not in failed_names]

        signatures_info = f"Merged {len(succeeded_names)} file(s): {', '.join(succeeded_names)}"
        return [{'signatures_data': df_signatures.to_dict('records'), 'filename': succeeded_names, 'info': signatures_info}]
    else:
        return dash.no_update

@app.callback(
    Output('upload-error-message-1', 'children'),
    Input('upload-data-1-signatures', 'contents'),
    State('upload-data-1-signatures', 'filename'),
    prevent_initial_call=True
)
def show_upload_status(contents, filename):
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
    Output('example-set-blurb', 'children'),
    Input('example-set-select', 'value'),
)
def describe_example_set(example_set):
    return EXAMPLE_SET_BLURBS.get(example_set, '')


@app.callback(
    [Output('session-1-signatures', 'data', allow_duplicate=True),
     Output('upload-error-message-1', 'children', allow_duplicate=True),
     Output('toggle-heatmap', 'checked', allow_duplicate=True),
     Output('auto-reload-armed', 'data', allow_duplicate=True)],
    Input('load-example-btn', 'n_clicks'),
    State('example-set-select', 'value'),
    prevent_initial_call=True,
    running=[
        (Output('load-example-btn', 'loading'), True, False),
        (Output('load-example-btn', 'disabled'), True, False),
    ],
)
def load_example_dataset(n_clicks, example_set):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    example_set = example_set or DEFAULT_EXAMPLE_SET
    spec = EXAMPLE_SIGNATURE_SETS.get(example_set, {})
    label = spec.get('label', example_set)

    try:
        df_signatures, filenames = load_example_merged_signatures(example_set=example_set)
    except (OSError, ValueError) as e:
        alert = dmc.Alert(
            f"Could not load '{label}': {e}",
            icon=DashIconify(icon="tabler:alert-circle", width=18),
            title="Error",
            color="red",
            withCloseButton=True
        )
        return dash.no_update, alert, dash.no_update, dash.no_update

    n_signatures = df_signatures.shape[1] - 1  # minus the 'Type' column
    info = f"Loaded dataset: {label} ({', '.join(filenames)})"

    body = [
        dmc.Text(f"{label} — {n_signatures} signatures from "
                 f"{len(filenames)} file(s): {', '.join(filenames)}", size="sm"),
    ]
    if n_signatures > LEGIBLE_SIGNATURE_LIMIT:
        body.append(dmc.Text(
            f"That is more than {LEGIBLE_SIGNATURE_LIMIT} signatures, so heatmap labels "
            "will be small. Narrow the selection in 'Select Signatures' to read them.",
            size="xs", c="dimmed", style={"marginTop": "0.25rem"}))

    alert = dmc.Alert(
        body,
        icon=DashIconify(icon="tabler:check-circle", width=18),
        title="Dataset Loaded",
        color="blue",
        withCloseButton=True
    )
    return {'signatures_data': df_signatures.to_dict('records'), 'filename': filenames, 'info': info}, alert, False, True


@app.callback(
    Output('signature-legibility-warning', 'children'),
    Input('signatures-dropdown-1', 'value'),
)
def warn_on_signature_count(selected_signatures):
    """The clustered heatmap drops to ~6px labels past ~40 signatures. Say so
    instead of silently rendering an unreadable plot."""
    n = len(selected_signatures or [])
    if n <= LEGIBLE_SIGNATURE_LIMIT:
        return ''
    return dmc.Alert(
        f"{n} signatures selected. Above {LEGIBLE_SIGNATURE_LIMIT} the heatmap and "
        "dendrogram labels become too small to read, and clustering gets slow — "
        "deselect some, or load a smaller dataset.",
        icon=DashIconify(icon="tabler:alert-triangle", width=18),
        color="yellow",
        withCloseButton=True,
        style={"marginTop": "0.5rem"},
    )

@app.callback(
    [Output('session-1-signatures', 'data', allow_duplicate=True),
     Output('upload-data-1-signatures', 'contents'),
     Output('upload-error-message-1', 'children', allow_duplicate=True),
     Output('auto-reload-armed', 'data', allow_duplicate=True)],
    Input('clear-upload-btn', 'n_clicks'),
    prevent_initial_call=True,
)
def clear_uploaded_signatures(n_clicks):
    if not n_clicks:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    return None, None, '', True


@app.callback(
    Output('reload-signal', 'data'),
    Output('auto-reload-armed', 'data', allow_duplicate=True),
    Input('signatures-dropdown-1', 'value'),
    State('auto-reload-armed', 'data'),
    State('reload-signal', 'data'),
    prevent_initial_call=True,
)
def fire_auto_reload(_, armed, signal):
    if not armed:
        return dash.no_update, dash.no_update
    return (signal or 0) + 1, False


@app.callback(
    Output("collapse-form", "opened"),
    [Input("toggle-button", "n_clicks")],
    [State("collapse-form", "opened")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open



# Placeholder state (no figure yet). Height matches the clustermap's floor so
# the box never shrinks below what plotly needs: a real figure arriving into a
# short box aborts its own render, and the graph then stays blank.
_EMPTY_GRAPH_STYLE = {"width": "100%", "height": f"{MIN_FIGURE_SIZE}px"}


def _graph_style(fig):
    """Build the dcc.Graph style from the size range the figure carries in
    layout.meta: fill the container, but stay square and clamped between the
    readability floor (scroll appears below it) and the max useful size."""
    meta = fig.layout.meta or {}
    return {
        "width": "100%",
        "minWidth": f"{meta.get('min_size', MIN_FIGURE_SIZE)}px",
        "maxWidth": f"{meta.get('max_size', 1400)}px",
        "minHeight": f"{MIN_FIGURE_SIZE}px",
        "aspectRatio": "1 / 1",
        "margin": "0 auto",
    }


@app.callback(
    [Output('form-output', 'children'),
     Output('heatmap-plot', 'figure'),
     Output('heatmap-reprint-plot', 'figure'),
     Output('heatmap-plot', 'style'),
     Output('heatmap-reprint-plot', 'style')],
    [Input('initial-load-1', 'n_intervals'),
     Input('reload-signal', 'data'),
     Input('submit-button', 'n_clicks'),
     Input("toggle-heatmap", "checked")],
    [State('dropdown-1', 'value'),
     State('signatures-dropdown-1', 'value'),
     State('distance-metric', 'value'),
     State('clustering-method', 'value'),
     State('epsilon', 'value'),
     State('cluster-threshold', 'value'),
     State('session-1-signatures', 'data'),
     State('paper-groups-switch', 'checked'),
     ],
    running=[
        (Output('submit-button', 'loading'), True, False),
        (Output('submit-button', 'disabled'), True, False),
    ],
)
def update_output(init_load, reload_signal, n_clicks, hide_heatmap, selected_file, selected_signatures, distance_metric, clustering_method, epsilon, cluster_threshold, signatures, show_paper_groups):
    trigger_id = ctx.triggered_id or 'initial-load-1'

    if not selected_signatures or not selected_file:
        return '', {}, {}, _EMPTY_GRAPH_STYLE, _EMPTY_GRAPH_STYLE

    functions = {'rmse': calculate_rmse, 'cosine': calculate_cosine, 'js_divergence': calculate_js_divergence}
    metric_labels = {'rmse': 'RMSE', 'cosine': 'Cosine', 'js_divergence': 'JS Divergence'}
    metric_label = metric_labels[distance_metric]

    if signatures is not None:
        data_df = pd.DataFrame(signatures['signatures_data'])
        data_df.index = data_df['Type']
        data_df = data_df.drop(columns='Type')[selected_signatures]
    else:
        data_df = pd.read_csv(f"data/signatures/{selected_file}", sep='\t', index_col=0)[selected_signatures]

    # GnBu for the signatures, OrRd for the RePrints: the ColorBrewer ramps the
    # published figures use, so the two can be compared side by side.
    annotation_groups = PAPER_GOLD_STANDARD_GROUPS if show_paper_groups else None

    df_reprint = reprint(data_df, epsilon=epsilon)
    fig_sig = create_heatmap_with_custom_sim(data_df, calc_func=functions[distance_metric], colorscale=GNBU_9, hide_heatmap=hide_heatmap, method=clustering_method, cluster_threshold_frac=cluster_threshold, metric_label=metric_label, annotation_groups=annotation_groups)
    fig_rep = create_heatmap_with_custom_sim(df_reprint, calc_func=functions[distance_metric], colorscale=ORRD_9, hide_heatmap=hide_heatmap, method=clustering_method, cluster_threshold_frac=cluster_threshold, metric_label=metric_label, annotation_groups=annotation_groups)
    return (f'Distance Metric: {distance_metric}, Clustering Method: {clustering_method}, Epsilon: {epsilon}',
            fig_sig, fig_rep, _graph_style(fig_sig), _graph_style(fig_rep))

@app.callback(
    [Output('signatures-dropdown-1', 'options'),
     Output('signatures-dropdown-1', 'value'),
     Output('dropdown-1', 'style'),
     Output('info_uploader', 'children'),
     Output('clear-upload-btn', 'style'),
     Output('clear-upload-hint', 'style'),
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

        # Use the uploaded file name(s) (without extension) as prefix
        base_name = _merged_base_name(contents.get('filename'))
        filename = f"{base_name}_reprints.csv"

        return dcc.send_data_frame(df_reprint.to_csv, filename=filename)
    else:
        df_signatures = pd.read_csv(f"data/signatures/{selected_file}", sep='\t', index_col=0)[selected_signatures]
        df_reprint = reprint(df_signatures, epsilon=epsilon)

        df_reprint.columns = [f"reprint_{col}" for col in df_reprint.columns]

        # Use the reference signatures file name (without extension) as prefix
        base_name = selected_file or "reprints"
        if isinstance(base_name, str) and '.' in base_name:
            base_name = base_name.rsplit('.', 1)[0]
        filename = f"{base_name}_reprints.csv"

        return dcc.send_data_frame(df_reprint.to_csv, filename=filename)


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
        uploaded_names = session_contents["filename"]
        uploaded_names = uploaded_names if isinstance(uploaded_names, list) else [uploaded_names]
        return ", ".join(uploaded_names), f"{len(sig_cols)} signatures"
    if selected_file and selected_file in data:
        count = len(data[selected_file])
        return selected_file, f"{count} signatures"
    return "None", "0"


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


def _empty_heatmap_fig():
    """Return an empty figure with a reload prompt message"""
    empty_fig = go.Figure()
    empty_fig.update_layout(
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[{
            'text': 'Click "Reload Heatmaps" to generate new plots',
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
    return empty_fig


@app.callback(
    [Output('heatmap-plot', 'figure', allow_duplicate=True),
     Output('heatmap-reprint-plot', 'figure', allow_duplicate=True),
     Output('heatmap-plot', 'style', allow_duplicate=True),
     Output('heatmap-reprint-plot', 'style', allow_duplicate=True)],
    [Input('distance-metric', 'value'),
     Input('clustering-method', 'value'),
     Input('epsilon', 'value'),
     Input('cluster-threshold', 'value')],
    prevent_initial_call=True
)
def clear_plots_on_parameter_change(distance_metric, clustering_method, epsilon, cluster_threshold):
    """Clear plots when parameters change to avoid showing outdated data"""
    return _empty_heatmap_fig(), _empty_heatmap_fig(), _EMPTY_GRAPH_STYLE, _EMPTY_GRAPH_STYLE


@app.callback(
    [Output('heatmap-plot', 'figure', allow_duplicate=True),
     Output('heatmap-reprint-plot', 'figure', allow_duplicate=True),
     Output('heatmap-plot', 'style', allow_duplicate=True),
     Output('heatmap-reprint-plot', 'style', allow_duplicate=True)],
    Input('signatures-dropdown-1', 'value'),
    prevent_initial_call=True
)
def clear_plots_on_signature_change(selected_signatures):
    """Clear plots when signature selection changes"""
    return _empty_heatmap_fig(), _empty_heatmap_fig(), _EMPTY_GRAPH_STYLE, _EMPTY_GRAPH_STYLE


@app.callback(
    [Output('heatmap-plot', 'figure', allow_duplicate=True),
     Output('heatmap-reprint-plot', 'figure', allow_duplicate=True),
     Output('heatmap-plot', 'style', allow_duplicate=True),
     Output('heatmap-reprint-plot', 'style', allow_duplicate=True)],
    Input('dropdown-1', 'value'),
    prevent_initial_call=True
)
def clear_plots_on_file_change(selected_file):
    """Clear plots when reference file changes"""
    return _empty_heatmap_fig(), _empty_heatmap_fig(), _EMPTY_GRAPH_STYLE, _EMPTY_GRAPH_STYLE


@app.callback(
    [Output('heatmap-plot', 'figure', allow_duplicate=True),
     Output('heatmap-reprint-plot', 'figure', allow_duplicate=True),
     Output('heatmap-plot', 'style', allow_duplicate=True),
     Output('heatmap-reprint-plot', 'style', allow_duplicate=True)],
    Input('session-1-signatures', 'data'),
    prevent_initial_call=True
)
def clear_plots_on_upload(uploaded_data):
    """Clear plots when new signatures are uploaded"""
    if uploaded_data is not None:
        return _empty_heatmap_fig(), _empty_heatmap_fig(), _EMPTY_GRAPH_STYLE, _EMPTY_GRAPH_STYLE
    return dash.no_update, dash.no_update, dash.no_update, dash.no_update