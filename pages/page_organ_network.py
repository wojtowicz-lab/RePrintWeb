from utils.organ_network import build_organ_similarity_graph, group_by_refsig, list_available_organs
from utils.community import create_community_graph_figure, empty_community_fig, palette
from main import app
from dash import dcc, html, Input, Output, State
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from pages.nav import navbar
import pandas as pd
import dash


ALL_ORGANS = list_available_organs()

COLORS = {
    "primary_blue": "#2563EB",
    "bg_light": "#F8FAFC",
    "white": "#FFFFFF",
    "navy": "#1E293B",
    "teal": "#14B8A6",
    "red": "#E11D48",
    "text_primary": "#1F2937",
    "text_secondary": "#6B7280",
    "border": "#E5E7EB",
    "shadow": "0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04)",
}

# ============================================================================
# APPLICATION LAYOUT
# ============================================================================
page_organ_network_layout = html.Div([
    navbar,

    dmc.Container(
        size="xl",
        style={"backgroundColor": COLORS["bg_light"], "minHeight": "100vh", "paddingTop": "3rem", "paddingBottom": "3rem"},
        children=[
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
                                                DashIconify(icon="tabler:topology-star-3", width=20, height=20, color=COLORS["primary_blue"]),
                                                html.H5("Organ Signature Network", style={"margin": 0, "fontWeight": "600"}),
                                            ]
                                        ),
                                    ),
                                    dmc.AccordionPanel(
                                        children=[
                                            html.P(
                                                [
                                                    "Replicates the network idea from ",
                                                    html.Strong("Degasperi et al. 2022 (Nat Cancer), Fig. 2k / Fig. 3"),
                                                    ": each node is one organ-specific mutational signature (bundled dataset, ",
                                                    html.Code("data/signatures_organ/version_1"),
                                                    ", 21 organs). Nodes are colored by the reference signature (\"RefSig\") each one "
                                                    "is already labeled with in the source data - this is known from the original "
                                                    "analysis, not something Louvain discovers here.",
                                                ],
                                                style={"fontSize": "0.95rem", "marginBottom": "0.75rem"}
                                            ),
                                            html.P(
                                                [
                                                    "An edge connects two signatures from ", html.Strong("different organs"),
                                                    " two ways, matching the paper: ", html.Strong("direct"),
                                                    " - cosine similarity between them alone clears the threshold below - or ",
                                                    html.Strong("combination"),
                                                    " - a convex mix of two same-organ signatures (w·A + (1-w)·C) reconstructs the "
                                                    "target at or above that threshold, and one of A/C supplies at least 65% of the "
                                                    "mix. The combination rule is what makes the network mostly one connected graph "
                                                    "rather than many small disconnected pieces, since a signature can be a genuine "
                                                    "mixture that no single other signature matches closely on its own. Edges are "
                                                    "rendered undirected here (both kinds pooled into one graph); the dominant "
                                                    "contributor and mix weight for combination edges are in the downloaded CSV.",
                                                ],
                                                style={"fontSize": "0.9rem", "color": COLORS["text_secondary"], "marginBottom": 0}
                                            ),
                                        ]
                                    ),
                                ],
                            ),
                        ]
                    ),
                ]
            ),

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
                                    dmc.Text("Organs to Include", size="sm", fw=600, style={"marginBottom": "0.5rem"}),
                                    dcc.Dropdown(
                                        id='organ-select-network',
                                        options=[{'label': o.replace('_', ' '), 'value': o} for o in ALL_ORGANS],
                                        multi=True,
                                        value=ALL_ORGANS,
                                        placeholder="Choose organs...",
                                    ),
                                ]
                            ),
                            dmc.GridCol(
                                span=12,
                                children=[
                                    dmc.Text("Minimum Cosine Similarity", size="sm", fw=600, style={"marginBottom": "0.5rem"}),
                                    dmc.Slider(
                                        id="min-cosine-network",
                                        value=0.89,
                                        min=0.5,
                                        max=0.99,
                                        step=0.01,
                                        marks=[
                                            {"value": 0.5, "label": "0.5"},
                                            {"value": 0.89, "label": "0.89 (paper)"},
                                            {"value": 0.99, "label": "0.99"},
                                        ],
                                        style={"width": "100%", "marginBottom": "1.5rem"}
                                    ),
                                    dmc.Text(
                                        "Only cross-organ pairs at or above this cosine similarity get an edge. Degasperi et al. use 0.89.",
                                        size="xs",
                                        c="dimmed",
                                    ),
                                ]
                            ),
                        ],
                        grow=True,
                    ),
                ]
            ),

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
                                "Download Group Assignments",
                                id="btn_csv-organ-network",
                                color="teal",
                                size="md",
                                style={"backgroundColor": COLORS["teal"]},
                                leftSection=DashIconify(icon="tabler:download", width=18),
                            ),
                            dmc.Button(
                                "Download Edges",
                                id="btn_csv-organ-network-edges",
                                color="gray",
                                size="md",
                                leftSection=DashIconify(icon="tabler:download", width=18),
                            ),
                            dmc.Button(
                                "Build Network",
                                id="submit-button-organ-network",
                                color="red",
                                size="md",
                                style={"backgroundColor": COLORS["red"]},
                                leftSection=DashIconify(icon="tabler:topology-star-3", width=18),
                            ),
                        ]
                    ),
                ]
            ),

            html.Div(id='form-output-organ-network'),

            dmc.Card(
                style={
                    "backgroundColor": COLORS["white"],
                    "border": f"1px solid {COLORS['border']}",
                    "boxShadow": COLORS["shadow"],
                    "borderRadius": "0.75rem",
                    "padding": "1.5rem",
                },
                children=[
                    dcc.Loading(
                        id="loading-organ-network",
                        type="default",
                        children=dcc.Graph(
                            id='organ-network-graph',
                            figure=empty_community_fig("Click \"Build Network\" to compute the similarity graph"),
                            config={
                                'displayModeBar': True,
                                'displaylogo': False,
                                'modeBarButtonsToAdd': ['toImage'],
                                'toImageButtonOptions': {
                                    'format': 'png',
                                    'filename': 'organ_signature_network',
                                    'height': 900,
                                    'width': 1200,
                                    'scale': 2
                                }
                            }
                        )
                    ),
                    html.Div(id='organ-network-group-list', style={"marginTop": "1rem"}),
                ]
            ),

            dcc.Store(id='organ-network-assignments-store', data=None),
            dcc.Store(id='organ-network-edges-store', data=None),
            dcc.Interval(id='initial-load-organ-network', interval=1000, n_intervals=0, max_intervals=1),
            dcc.Download(id="download-organ-network-csv"),
            dcc.Download(id="download-organ-network-edges-csv"),
        ]
    ),
])


def _group_badges(communities, labels):
    items = []
    colors = palette(len(communities))
    for cid, (members, label) in enumerate(zip(communities, labels), start=1):
        color = colors[cid - 1]
        items.append(
            dmc.Group(
                gap="xs",
                align="flex-start",
                wrap="nowrap",
                style={"marginBottom": "0.4rem"},
                children=[
                    dmc.Badge(f"{label} (n={len(members)})", color="gray", variant="filled",
                               style={"backgroundColor": color, "flexShrink": 0}),
                    dmc.Text(", ".join(sorted(members)), size="xs", c=COLORS["text_secondary"]),
                ]
            )
        )
    return items


@app.callback(
    [Output('form-output-organ-network', 'children'),
     Output('organ-network-graph', 'figure'),
     Output('organ-network-group-list', 'children'),
     Output('organ-network-assignments-store', 'data'),
     Output('organ-network-edges-store', 'data')],
    [Input('initial-load-organ-network', 'n_intervals'),
     Input('submit-button-organ-network', 'n_clicks')],
    [State('organ-select-network', 'value'),
     State('min-cosine-network', 'value')],
    running=[
        (Output('submit-button-organ-network', 'loading'), True, False),
        (Output('submit-button-organ-network', 'disabled'), True, False),
    ],
)
def update_organ_network(init_load, n_clicks, organs, min_similarity):
    if not organs:
        return '', empty_community_fig("Select at least one organ"), '', dash.no_update, dash.no_update

    G, meta = build_organ_similarity_graph(min_similarity=min_similarity, organs=organs)
    communities, labels, mod_score = group_by_refsig(G, meta)

    fig = create_community_graph_figure(
        G, communities, mod_score, seed=42,
        title="Organ Signature Network",
        community_labels=labels,
        unit_noun='group',
    )

    n_isolated = sum(1 for n in G.nodes() if G.degree(n) == 0)
    n_direct_only = sum(1 for _, _, d in G.edges(data=True) if d.get('kind') == 'direct')
    n_combo_only = sum(1 for _, _, d in G.edges(data=True) if d.get('kind') == 'combination')
    n_both = sum(1 for _, _, d in G.edges(data=True) if d.get('kind') == 'both')
    summary = (f"{G.number_of_nodes()} signatures across {len(organs)} organs, {G.number_of_edges()} edges "
               f"({n_direct_only} direct-only, {n_combo_only} combination-only, {n_both} both, cosine ≥ {min_similarity}), "
               f"{n_isolated} with no cross-organ match at this threshold.")

    assignments = {
        'Signature': list(G.nodes()),
        'Organ': [meta[n]['organ'] for n in G.nodes()],
        'RefSig': [meta[n]['refsig'] for n in G.nodes()],
        'Degree': [G.degree(n) for n in G.nodes()],
    }

    edges = {
        'Source': [u for u, v, d in G.edges(data=True)],
        'Target': [v for u, v, d in G.edges(data=True)],
        'Kind': [d.get('kind', 'direct') for u, v, d in G.edges(data=True)],
        'CosineSimilarity': [round(d.get('weight', 0), 4) for u, v, d in G.edges(data=True)],
        'DominantContribution': [round(d['contribution'], 3) if 'contribution' in d else '' for u, v, d in G.edges(data=True)],
    }

    return summary, fig, _group_badges(communities, labels), assignments, edges


@app.callback(
    [Output('organ-network-graph', 'figure', allow_duplicate=True)],
    [Input('organ-select-network', 'value'),
     Input('min-cosine-network', 'value')],
    prevent_initial_call=True
)
def clear_plot_on_parameter_change_organ_network(*_):
    return [empty_community_fig("Click \"Build Network\" to apply the new parameters")]


@app.callback(
    Output("download-organ-network-csv", "data"),
    Input("btn_csv-organ-network", "n_clicks"),
    State('organ-network-assignments-store', 'data'),
    prevent_initial_call=True
)
def download_organ_network_csv(n_clicks, assignments):
    if not assignments:
        return dash.no_update
    df = pd.DataFrame(assignments)
    return dcc.send_data_frame(df.to_csv, filename="organ_network_groups.csv", index=False)


@app.callback(
    Output("download-organ-network-edges-csv", "data"),
    Input("btn_csv-organ-network-edges", "n_clicks"),
    State('organ-network-edges-store', 'data'),
    prevent_initial_call=True
)
def download_organ_network_edges_csv(n_clicks, edges):
    if not edges:
        return dash.no_update
    df = pd.DataFrame(edges)
    return dcc.send_data_frame(df.to_csv, filename="organ_network_edges.csv", index=False)
