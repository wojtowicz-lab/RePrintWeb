import colorsys
import itertools

import numpy as np
import networkx as nx
import plotly.graph_objects as go
from networkx.algorithms.community import louvain_communities, modularity

from utils.utils import calculate_rmse

DEFAULT_K = 8

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


def build_similarity_graph(df, calc_func=calculate_rmse, k=DEFAULT_K, mutual=True):
    """
    Build a weighted undirected graph over the signatures/samples (columns
    of df) as a mutual k-nearest-neighbour graph. Pairwise distances from
    calc_func are min-max normalized to [0, 1] and inverted into a
    similarity weight, then each node keeps an edge to its `k` most similar
    neighbours; with `mutual=True` the edge survives only if both endpoints
    picked each other.
    """
    labels, dist_matrix = _pairwise_distance_matrix(df, calc_func)
    n = len(labels)

    if n == 0:
        return nx.Graph(), labels, dist_matrix

    d_min, d_max = dist_matrix.min(), dist_matrix.max()
    if d_max > d_min:
        sim_matrix = 1 - (dist_matrix - d_min) / (d_max - d_min)
    else:
        sim_matrix = np.ones_like(dist_matrix)
    np.fill_diagonal(sim_matrix, 0)

    G = nx.Graph()
    G.add_nodes_from(labels)

    if n > 1:
        k = max(1, min(int(k), n - 1))
        # -1 on the diagonal so a node is never its own nearest neighbour.
        ranking = np.where(np.eye(n, dtype=bool), -1.0, sim_matrix)
        neighbours = [set(np.argsort(-ranking[i])[:k].tolist()) for i in range(n)]

        for i in range(n):
            for j in neighbours[i]:
                if i == j or (mutual and i not in neighbours[j]):
                    continue
                w = sim_matrix[i, j]
                if w > 0:
                    G.add_edge(labels[i], labels[j], weight=float(w))

    return G, labels, sim_matrix


def detect_communities(df, calc_func=calculate_rmse, resolution=1.0, k=DEFAULT_K, mutual=True, seed=42):
    """
    Run Louvain community detection on the mutual-kNN similarity graph.

    Returns (G, communities, community_of, mod_score):
      - communities: list[set[str]], largest community first
      - community_of: dict label -> 1-based community id (matches order in `communities`)
      - mod_score: modularity of the partition, or None when it isn't meaningful
        (fewer than 2 nodes, or no edges at all)
    """
    G, labels, _ = build_similarity_graph(df, calc_func, k=k, mutual=mutual)

    if G.number_of_nodes() == 0:
        return G, [], {}, None

    if G.number_of_edges() == 0:
        # Only reachable with a single node, or when mutual=True and no pair
        # picked each other (k=1 on an odd similarity structure).
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

NODE_GAP = 1.0
BLOB_GAP = 1.5 * NODE_GAP


def _spread_nodes(pos, min_dist, iterations=80, seed=42):
    """
    Push apart every pair of nodes closer than min_dist, repeatedly, until
    no pair is. Force layouts (and Kamada-Kawai even more so) are happy to
    stack near-identical nodes on top of each other, which turns into a
    single unreadable label clump; this is the cheap fix. Nodes that
    coincide exactly get a deterministic nudge first so they have a
    direction to separate along.
    """
    nodes = list(pos)
    if len(nodes) < 2:
        return dict(pos)
    rng = np.random.default_rng(seed)
    xy = np.array([pos[n] for n in nodes], dtype=float)
    for _ in range(iterations):
        diff = xy[:, None, :] - xy[None, :, :]
        dist = np.hypot(diff[..., 0], diff[..., 1])
        np.fill_diagonal(dist, np.inf)
        coincident = dist < 1e-9
        if coincident.any():
            xy += rng.normal(scale=min_dist * 0.05, size=xy.shape)
            continue
        close = dist < min_dist
        if not close.any():
            break
        overlap = np.zeros_like(dist)
        overlap[close] = (min_dist - dist[close]) / dist[close]
        xy += 0.5 * (diff * overlap[..., None]).sum(axis=1)
    return {n: (float(x), float(y)) for n, (x, y) in zip(nodes, xy)}


def _local_layout(subG, seed=42):
    """
    Lay out one group of nodes (a community, or a whole component that is
    a single community) around the origin, with members at least NODE_GAP
    apart. Kamada-Kawai on hop distance spreads a small dense group far
    more evenly than a weighted spring layout, which pulls the most
    similar members into one pile at the centre; the weights are still
    what decided the grouping, they just don't also decide the picture.
    Returns (positions, radius) where radius is the actual extent from the
    centroid, so the caller can pack groups by their real footprint.
    """
    n = subG.number_of_nodes()
    if n == 1:
        return {next(iter(subG.nodes())): (0.0, 0.0)}, NODE_GAP * 0.5

    scale = max(NODE_GAP, 0.62 * NODE_GAP * np.sqrt(n))
    if nx.is_connected(subG):
        local = nx.kamada_kawai_layout(subG, weight=None, scale=scale)
    else:
        local = nx.spring_layout(subG, weight='weight', seed=seed, k=NODE_GAP, scale=scale, iterations=200)
    local = _spread_nodes(local, NODE_GAP, seed=seed)

    xy = np.array(list(local.values()))
    centre = xy.mean(axis=0)
    local = {node: (x - centre[0], y - centre[1]) for node, (x, y) in local.items()}
    radius = max(np.hypot(x, y) for x, y in local.values()) + NODE_GAP * 0.5
    return local, radius


def _relax_centres(centres, radii, iterations=200):
    """
    Push apart any two group centres whose blobs (radius + BLOB_GAP/2
    each) overlap, and leave every other pair alone. Returns the new
    centres and whether anything still overlapped on the last pass.
    """
    ids = list(centres)
    xy = np.array([centres[c] for c in ids], dtype=float)
    r = np.array([radii[c] for c in ids], dtype=float) + BLOB_GAP / 2
    need = r[:, None] + r[None, :]
    for _ in range(iterations):
        diff = xy[:, None, :] - xy[None, :, :]
        dist = np.hypot(diff[..., 0], diff[..., 1])
        np.fill_diagonal(dist, np.inf)
        close = dist < need
        if not close.any():
            break
        overlap = np.zeros_like(dist)
        overlap[close] = (need[close] - dist[close]) / np.maximum(dist[close], 1e-9)
        xy += 0.5 * (diff * overlap[..., None]).sum(axis=1)
    return {c: (float(x), float(y)) for c, (x, y) in zip(ids, xy)}


def _compact_centres(centres, radii, rounds=40, shrink=0.92):
    """
    Alternate pulling every centre toward the common centroid with
    pushing overlapping blobs back apart (_relax_centres). Overlap removal
    alone only ever spreads things out, so whatever slack the initial
    spring layout left between blobs stays there - typically a big empty
    hole in the middle with the blobs on a ring around it. Shrinking then
    re-separating a few dozen times closes that slack while keeping the
    neighbour relationships the spring layout chose; blobs end up as
    tightly packed as their radii allow, which is what maximises the
    pixels each node gets once Plotly fits the whole picture to the plot.
    """
    ids = list(centres)
    for _ in range(rounds):
        xy = np.array([centres[c] for c in ids], dtype=float)
        centroid = xy.mean(axis=0)
        pulled = {c: tuple(centroid + (np.array(centres[c]) - centroid) * shrink) for c in ids}
        centres = _relax_centres(pulled, radii)
    return centres


def _community_cluster_layout(G, node_communities, seed=42):
    """
    Two-level layout so same-community nodes visually stay together as a
    blob, instead of a plain spring_layout - which only pulls on individual
    edges and happily lets a community's nodes drift apart if they also
    have decent similarity to nodes outside their community (common, since
    Louvain's grouping is a "best split", not a guarantee that off-community
    similarity is negligible).

    Step 1: lay out each community on its own (_local_layout), which also
    tells us how big its blob really is.
    Step 2: collapse each community to a single super-node and spring-layout
    those so related communities land near each other, then scale that
    only as far as the *typical* pair needs, then squeeze the blobs
    together as far as they go without overlapping (_compact_centres), so
    blobs are separated but not scattered.

    `node_communities` may cover more nodes than G has (the caller reuses
    one global community map across each connected component separately) -
    community ids are restricted to G's own nodes below, otherwise a
    community with zero members in this particular G would still get a
    meta-graph slot and an empty local layout.
    """
    communities = sorted({node_communities[n] for n in G.nodes()})
    members_by_community = {cid: [n for n in G.nodes() if node_communities[n] == cid] for cid in communities}

    if len(communities) <= 1:
        local, _ = _local_layout(G, seed=seed)
        return local

    local_layouts, radius = {}, {}
    for cid, members in members_by_community.items():
        local_layouts[cid], radius[cid] = _local_layout(G.subgraph(members), seed=seed)

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

    # Scale so the median pair of communities is just clear of each other;
    # _relax_centres then handles the pairs that are still too close.
    ratios = []
    for a, b in itertools.combinations(communities, 2):
        ax, ay = meta_pos_raw[a]
        bx, by = meta_pos_raw[b]
        raw_dist = max(np.hypot(ax - bx, ay - by), 1e-6)
        ratios.append((radius[a] + radius[b] + BLOB_GAP) / raw_dist)
    meta_scale = float(np.median(ratios))
    centres = {cid: (x * meta_scale, y * meta_scale) for cid, (x, y) in meta_pos_raw.items()}
    centres = _compact_centres(centres, radius)

    positions = {}
    for cid in communities:
        cx, cy = centres[cid]
        for n, (x, y) in local_layouts[cid].items():
            positions[n] = (cx + x, cy + y)
    return positions


def _pack_components(layouts):
    """
    Place several independently laid-out pieces (connected components,
    which share no edge, so nothing should pull them toward or away from
    each other) into one compact picture. Each piece is treated as a disc
    around its own centroid; the biggest goes in the middle, the rest are
    seeded on a spiral around it by decreasing size and then squeezed in
    with the same pull-and-separate loop used for community blobs
    (_compact_centres). A shelf/grid packer was tried first and looked
    fine until one small piece wrapped to a new row: it then sat a full
    row-height below everything, leaving a huge empty band across the
    plot - which reads as a rendering glitch.
    """
    if not layouts:
        return {}

    pieces = []
    for local_pos in layouts:
        xy = np.array(list(local_pos.values()), dtype=float)
        centre = xy.mean(axis=0)
        centred = {n: (x - centre[0], y - centre[1]) for n, (x, y) in local_pos.items()}
        radius = max(np.hypot(x, y) for x, y in centred.values()) + NODE_GAP / 2
        pieces.append((centred, radius))
    pieces.sort(key=lambda t: -t[1])

    centres, radii = {}, {}
    golden = np.pi * (3 - np.sqrt(5))
    reach = 0.0
    for i, (_, r) in enumerate(pieces):
        if i == 0:
            centres[i] = (0.0, 0.0)
        else:
            reach += r
            centres[i] = (reach * np.cos(i * golden), reach * np.sin(i * golden))
        radii[i] = r
    centres = _compact_centres(centres, radii)

    positions = {}
    for i, (centred, _) in enumerate(pieces):
        cx, cy = centres[i]
        for n, (x, y) in centred.items():
            positions[n] = (cx + x, cy + y)
    return positions


def _compute_layout(G, node_communities, seed=42):
    """
    Layout entry point. Real connected components of G share no edge with
    each other, so nothing should visually pull them apart or together -
    each is laid out on its own (community-first, via
    _community_cluster_layout), then all of them are packed together
    (_pack_components) rather than positioned by a force layout that has
    no basis for placing unconnected pieces sensibly. Singleton components (a node with no surviving edge at
    all) go in their own tidy row beneath everything else, since even a
    1-node "component layout" carries no meaningful shape.
    """
    components = [c for c in nx.connected_components(G) if len(c) > 1]
    isolated = sorted(n for n in G.nodes() if G.degree(n) == 0)

    layouts = [_community_cluster_layout(G.subgraph(comp_nodes), node_communities, seed=seed)
               for comp_nodes in components]
    positions = _pack_components(layouts)

    if isolated:
        if positions:
            xs = [p[0] for p in positions.values()]
            ys = [p[1] for p in positions.values()]
            x_min, width, y_min = min(xs), max(max(xs) - min(xs), NODE_GAP), min(ys)
        else:
            x_min, width, y_min = 0.0, 4.0 * NODE_GAP, 0.0

        cell = NODE_GAP * 1.6
        cols = max(1, int(width // cell) + 1)
        for idx, node in enumerate(isolated):
            row, col = divmod(idx, cols)
            positions[node] = (x_min + col * cell, y_min - BLOB_GAP - cell * (row + 1))

    return positions


def _radial_text_positions(points):
    """
    One Plotly textposition per node, pointing away from the group's
    centroid: nodes on the top of a blob get their label above, nodes on
    the right get it to the right, and so on. With every label simply
    "top center" the labels of a blob's upper arc pile onto each other and
    the lower arc's labels sit on top of the blob's own edges; pushing
    each one outward keeps them over empty canvas instead.
    """
    if len(points) < 3:
        return 'top center'
    xy = np.array(points, dtype=float)
    centre = xy.mean(axis=0)
    compass = ['middle right', 'top right', 'top center', 'top left',
               'middle left', 'bottom left', 'bottom center', 'bottom right']
    positions = []
    for x, y in xy:
        dx, dy = x - centre[0], y - centre[1]
        if abs(dx) < 1e-9 and abs(dy) < 1e-9:
            positions.append('top center')
            continue
        angle = np.degrees(np.arctan2(dy, dx)) % 360
        positions.append(compass[int(((angle + 22.5) % 360) // 45)])
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


def create_community_graph_figure(G, communities, mod_score, seed=42, title=''):
    """Node-link plot of G, nodes colored by their Louvain community."""
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
        traces.append(go.Scatter(
            x=[pos[m][0] for m in members],
            y=[pos[m][1] for m in members],
            mode='markers+text' if style['show_labels'] else 'markers',
            text=members,
            textposition=_radial_text_positions([pos[m] for m in members]),
            textfont=dict(size=style['font_size']),
            marker=dict(size=style['marker_size'], color=color, line=dict(width=1.5, color='white')),
            name=f"Community {cid} (n={len(members)})",
            hovertext=[f"{m}<br>Community {cid}" for m in members],
            hoverinfo='text',
        ))

    subtitle = f"{len(communities)} communit{'y' if len(communities) == 1 else 'ies'}"
    if mod_score is not None:
        subtitle += f" · modularity {mod_score:.3f}"
    full_title = f"{title}<br><span style='font-size:11px;color:#6B7280'>{subtitle}</span>" if title else subtitle

    fig_size = int(min(950, max(550, 480 + 3.5 * G.number_of_nodes())))

    xs = [p[0] for p in pos.values()]
    ys = [p[1] for p in pos.values()]
    x_span = max(max(xs) - min(xs), NODE_GAP)
    y_span = max(max(ys) - min(ys), NODE_GAP)
    pad_x = x_span * (0.16 if style['show_labels'] else 0.04)
    pad_y = y_span * (0.07 if style['show_labels'] else 0.04)

    fig = go.Figure(data=traces)
    fig.update_layout(
        title=dict(text=full_title, font=dict(size=14)),
        showlegend=True,
        legend=dict(orientation='h', yanchor='top', y=-0.05, font=dict(size=10)),
        xaxis=dict(visible=False, showgrid=False, zeroline=False,
                   range=[min(xs) - pad_x, max(xs) + pad_x]),
        yaxis=dict(visible=False, showgrid=False, zeroline=False,
                   range=[min(ys) - pad_y, max(ys) + pad_y]),
        hovermode='closest',
        margin=dict(l=20, r=20, t=60, b=20),
        height=fig_size,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig
