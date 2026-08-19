import colorsys
import itertools

import numpy as np
import networkx as nx
import plotly.graph_objects as go
from networkx.algorithms.community import louvain_communities, modularity

from utils.utils import calculate_rmse

# Qualitative palette for community colors, used as-is up to this many
# groups; beyond that palette() generates evenly spaced hues instead.
COMMUNITY_COLORS = [
    '#2563EB', '#E11D48', '#14B8A6', '#F59E0B', '#8B5CF6',
    '#10B981', '#EF4444', '#3B82F6', '#EC4899', '#84CC16',
    '#06B6D4', '#F97316',
]


def palette(n):
    if n <= len(COMMUNITY_COLORS):
        return COMMUNITY_COLORS[:n]
    colors = []
    for i in range(n):
        r, g, b = colorsys.hls_to_rgb(i / n, 0.55, 0.65)
        colors.append('#{:02x}{:02x}{:02x}'.format(int(r * 255), int(g * 255), int(b * 255)))
    return colors


def _pairwise_distance_matrix(df, calc_func):
    """Same transpose + pairwise distance computation used for the
    hierarchical-clustering heatmap, factored out so both approaches read
    the same distances."""
    df = df.T
    labels = df.index.tolist()
    n = df.shape[0]
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = calc_func(df.iloc[i, :], df.iloc[j, :])
            dist_matrix[i, j] = d
            dist_matrix[j, i] = d
    return labels, dist_matrix


def build_similarity_graph(df, calc_func=calculate_rmse, min_similarity=0.0):
    """
    Build a weighted undirected graph over the signatures/samples (columns
    of df). Pairwise distances from calc_func are min-max normalized to
    [0, 1] and inverted into a similarity weight, so min_similarity means
    the same thing regardless of which distance metric was used. An edge is
    added only when its similarity clears min_similarity.
    """
    labels, dist_matrix = _pairwise_distance_matrix(df, calc_func)
    n = len(labels)

    d_min, d_max = dist_matrix.min(), dist_matrix.max()
    if d_max > d_min:
        sim_matrix = 1 - (dist_matrix - d_min) / (d_max - d_min)
    else:
        sim_matrix = np.ones_like(dist_matrix)
    np.fill_diagonal(sim_matrix, 0)

    G = nx.Graph()
    G.add_nodes_from(labels)
    for i in range(n):
        for j in range(i + 1, n):
            w = sim_matrix[i, j]
            if w > 0 and w >= min_similarity:
                G.add_edge(labels[i], labels[j], weight=float(w))

    return G, labels, sim_matrix


def detect_communities(df, calc_func=calculate_rmse, resolution=1.0, min_similarity=0.0, seed=42):
    """
    Run Louvain community detection on the signature similarity graph.

    Returns (G, communities, community_of, mod_score):
      - communities: list[set[str]], largest community first
      - community_of: dict label -> 1-based community id (matches order in `communities`)
      - mod_score: modularity of the partition, or None when it isn't meaningful
        (fewer than 2 nodes, or every node isolated by the similarity threshold)
    """
    G, labels, _ = build_similarity_graph(df, calc_func, min_similarity)

    if G.number_of_nodes() == 0:
        return G, [], {}, None

    if G.number_of_edges() == 0:
        # Nothing clears the similarity threshold: every node is its own community.
        communities = [{label} for label in labels]
    else:
        communities = louvain_communities(G, weight='weight', resolution=resolution, seed=seed)

    communities = sorted((set(c) for c in communities), key=len, reverse=True)
    community_of = {label: cid for cid, members in enumerate(communities, start=1) for label in members}

    mod_score = None
    if G.number_of_edges() > 0 and len(communities) > 1:
        mod_score = modularity(G, communities, weight='weight', resolution=resolution)

    return G, communities, community_of, mod_score


def empty_community_fig(message="Not enough data to build a graph"):
    fig = go.Figure()
    fig.update_layout(
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[{
            'text': message,
            'xref': 'paper', 'yref': 'paper',
            'x': 0.5, 'y': 0.5,
            'showarrow': False,
            'font': {'size': 16, 'color': '#666'},
        }],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=550,
    )
    return fig


def _community_cluster_layout(G, node_communities, seed=42):
    """
    Two-level layout so same-community nodes visually stay together as a
    blob, instead of a plain spring_layout - which only pulls on individual
    edges and happily lets a community's nodes drift apart if they also
    have decent similarity to nodes outside their community (common, since
    Louvain's grouping is a "best split", not a guarantee that off-community
    similarity is negligible).

    Step 1: collapse each community to a single super-node and spring-layout
    those, so communities land far apart from each other.
    Step 2: spring-layout each community's own nodes in isolation, then
    scale/offset that local layout around its super-node's position.

    `node_communities` may cover more nodes than G has (the caller reuses
    one global community map across each connected component separately) -
    community ids are restricted to G's own nodes below, otherwise a
    community with zero members in this particular G would still get a
    meta-graph slot and an empty local layout, which both wastes space and
    divides by zero when sizing that (empty) local layout.
    """
    communities = sorted({node_communities[n] for n in G.nodes()})
    members_by_community = {cid: [n for n in G.nodes() if node_communities[n] == cid] for cid in communities}

    if len(communities) <= 1:
        k = 2.5 / np.sqrt(max(G.number_of_nodes(), 1))
        return nx.spring_layout(G, weight='weight', seed=seed, k=k, iterations=200)

    meta_graph = nx.Graph()
    meta_graph.add_nodes_from(communities)
    for u, v, edata in G.edges(data=True):
        cu, cv = node_communities[u], node_communities[v]
        if cu != cv:
            w = edata.get('weight', 1.0)
            if meta_graph.has_edge(cu, cv):
                meta_graph[cu][cv]['weight'] += w
            else:
                meta_graph.add_edge(cu, cv, weight=w)

    meta_k = 3.0 / np.sqrt(len(communities))
    meta_pos_raw = nx.spring_layout(meta_graph, weight='weight', seed=seed, k=meta_k, iterations=300)

    # Each community's local footprint (computed before scaling, so the
    # scale step below can guarantee blobs actually clear each other
    # instead of just "usually" being far enough apart).
    radius = {cid: min(1.6, 0.4 + 0.14 * np.sqrt(len(members))) for cid, members in members_by_community.items()}

    # Pick the smallest uniform scale factor that keeps every pair of
    # community centers at least (sum of their radii * margin) apart, so
    # blobs never overlap regardless of how tightly spring_layout happened
    # to pack the meta-graph.
    margin = 1.8
    needed_scale = 1.0
    for a, b in itertools.combinations(communities, 2):
        ax, ay = meta_pos_raw[a]
        bx, by = meta_pos_raw[b]
        raw_dist = max(np.hypot(ax - bx, ay - by), 1e-6)
        required = margin * (radius[a] + radius[b]) / raw_dist
        needed_scale = max(needed_scale, required)
    meta_scale = min(needed_scale, 40.0)

    meta_pos = {cid: (x * meta_scale, y * meta_scale) for cid, (x, y) in meta_pos_raw.items()}

    positions = {}
    for cid in communities:
        members = members_by_community[cid]
        cx, cy = meta_pos[cid]
        if len(members) == 1:
            positions[members[0]] = (cx, cy)
            continue

        subG = G.subgraph(members)
        local_k = 1.0 / np.sqrt(len(members))
        local_pos = nx.spring_layout(subG, weight='weight', seed=seed, k=local_k, iterations=150)
        for n, (x, y) in local_pos.items():
            positions[n] = (cx + x * radius[cid], cy + y * radius[cid])

    return positions


def _pack_components(footprints, gap=0.8):
    """
    Shelf-pack a list of (positions_dict, width, height) - each already in
    its own local 0..width x 0..height coordinates - left to right, wrapping
    to a new row once a row gets too wide. Used so unrelated connected
    components (which share no edge, so nothing should pull them toward
    each other) end up as a tidy tiled grid instead of positioned by
    whatever spring_layout does with no force acting between them - the
    single biggest source of "this graph looks like it exploded randomly"
    complaints, since a naive layout is free to fling disconnected pieces
    arbitrarily far apart.
    """
    positions = {}
    if not footprints:
        return positions

    footprints = sorted(footprints, key=lambda t: -(t[1] * t[2]))
    total_area = sum(w * h for _, w, h in footprints)
    row_width = max(6.0, np.sqrt(total_area) * 1.8)

    cursor_x, cursor_y, row_height = 0.0, 0.0, 0.0
    for local_pos, w, h in footprints:
        if cursor_x > 0 and cursor_x + w > row_width:
            cursor_x = 0.0
            cursor_y -= row_height + gap
            row_height = 0.0
        for n, (x, y) in local_pos.items():
            positions[n] = (cursor_x + x, cursor_y + y)
        cursor_x += w + gap
        row_height = max(row_height, h)

    return positions


def _compute_layout(G, node_communities, seed=42):
    """
    Layout entry point. Real connected components of G share no edge with
    each other, so nothing should visually pull them apart or together -
    each is laid out on its own (community-first, via
    _community_cluster_layout, when it spans more than one community), then
    all of them are shelf-packed into a grid (_pack_components) rather than
    positioned by a force layout that has no basis for placing unconnected
    pieces sensibly. Singleton components (a node with no surviving edge at
    all) go in their own tidy row beneath everything else, since even a
    1-node "component layout" carries no meaningful shape.
    """
    components = [c for c in nx.connected_components(G) if len(c) > 1]
    isolated = sorted(n for n in G.nodes() if G.degree(n) == 0)

    footprints = []
    for comp_nodes in components:
        subG = G.subgraph(comp_nodes)
        if len({node_communities[n] for n in comp_nodes}) > 1:
            local_pos = _community_cluster_layout(subG, node_communities, seed=seed)
        else:
            k = 2.2 / np.sqrt(len(comp_nodes))
            local_pos = nx.spring_layout(subG, weight='weight', seed=seed, k=k, iterations=200)

        xs = [p[0] for p in local_pos.values()]
        ys = [p[1] for p in local_pos.values()]
        x_min, y_min = min(xs), min(ys)
        w = max(max(xs) - x_min, 0.6)
        h = max(max(ys) - y_min, 0.6)
        local_pos = {n: (x - x_min, y - y_min) for n, (x, y) in local_pos.items()}
        footprints.append((local_pos, w, h))

    positions = _pack_components(footprints)

    if isolated:
        if positions:
            xs = [p[0] for p in positions.values()]
            ys = [p[1] for p in positions.values()]
            x_min, width, y_min = min(xs), max(max(xs) - min(xs), 1.0), min(ys)
        else:
            x_min, width, y_min = 0.0, 4.0, 0.0

        cols = max(1, int(np.ceil(np.sqrt(len(isolated) * 1.5))))
        cell = max(width / cols, 0.4)
        for idx, node in enumerate(isolated):
            row, col = divmod(idx, cols)
            positions[node] = (x_min + col * cell, y_min - cell * 1.5 * (row + 1))

    return positions


def _marker_style(n_nodes):
    """Shrink markers/labels as the graph grows so a dense, well-connected
    core doesn't turn into a solid blob of overlapping dots and text."""
    if n_nodes <= 30:
        return dict(marker_size=16, font_size=9, show_labels=True)
    if n_nodes <= 60:
        return dict(marker_size=12, font_size=8, show_labels=True)
    if n_nodes <= 100:
        return dict(marker_size=9, font_size=7, show_labels=False)
    return dict(marker_size=7, font_size=7, show_labels=False)


def create_community_graph_figure(G, communities, mod_score, seed=42, title='', community_labels=None, unit_noun='community'):
    """
    Node-link plot of G, nodes colored by group. `communities` is
    Louvain output by default, but any list[set[node]] partition works -
    e.g. groups known in advance from the data itself (see
    utils/organ_network.py), in which case pass `community_labels` (one
    string per group, same order as `communities`) to name them instead of
    "Community N".
    """
    if G.number_of_nodes() == 0:
        return empty_community_fig()

    node_communities = {n: cid for cid, members in enumerate(communities, start=1) for n in members}
    if G.number_of_nodes() == 1:
        pos = {next(iter(G.nodes())): (0.0, 0.0)}
    else:
        pos = _compute_layout(G, node_communities, seed=seed)

    style = _marker_style(G.number_of_nodes())

    # Edges within a community are drawn darker than edges crossing between
    # communities, so the crossing edges don't visually blur the blobs the
    # layout just worked to separate.
    intra_x, intra_y, inter_x, inter_y = [], [], [], []
    for u, v in G.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        if node_communities.get(u) == node_communities.get(v):
            intra_x += [x0, x1, None]
            intra_y += [y0, y1, None]
        else:
            inter_x += [x0, x1, None]
            inter_y += [y0, y1, None]

    traces = [
        go.Scatter(
            x=inter_x, y=inter_y,
            mode='lines',
            line=dict(width=1, color='rgba(140,140,140,0.15)'),
            hoverinfo='none',
            showlegend=False,
        ),
        go.Scatter(
            x=intra_x, y=intra_y,
            mode='lines',
            line=dict(width=1, color='rgba(90,90,90,0.45)'),
            hoverinfo='none',
            showlegend=False,
        ),
    ]

    colors = palette(len(communities))
    for cid, members in enumerate(communities, start=1):
        members = sorted(members)
        color = colors[cid - 1]
        label = community_labels[cid - 1] if community_labels else f"Community {cid}"
        traces.append(go.Scatter(
            x=[pos[m][0] for m in members],
            y=[pos[m][1] for m in members],
            mode='markers+text' if style['show_labels'] else 'markers',
            text=members,
            textposition='top center',
            textfont=dict(size=style['font_size']),
            marker=dict(size=style['marker_size'], color=color, line=dict(width=1.5, color='white')),
            name=f"{label} (n={len(members)})",
            hovertext=[f"{m}<br>{label}" for m in members],
            hoverinfo='text',
        ))

    noun = unit_noun if len(communities) == 1 else (f"{unit_noun[:-1]}ies" if unit_noun.endswith('y') else f"{unit_noun}s")
    subtitle = f"{len(communities)} {noun}"
    if mod_score is not None:
        subtitle += f" · modularity {mod_score:.3f}"
    full_title = f"{title}<br><span style='font-size:11px;color:#6B7280'>{subtitle}</span>" if title else subtitle

    fig_size = int(min(950, max(550, 480 + 3.5 * G.number_of_nodes())))

    fig = go.Figure(data=traces)
    fig.update_layout(
        title=dict(text=full_title, font=dict(size=14)),
        showlegend=True,
        legend=dict(orientation='h', yanchor='top', y=-0.05, font=dict(size=10)),
        xaxis=dict(visible=False, showgrid=False, zeroline=False),
        yaxis=dict(visible=False, showgrid=False, zeroline=False),
        hovermode='closest',
        margin=dict(l=20, r=20, t=60, b=20),
        height=fig_size,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig
