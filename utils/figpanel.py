import plotly.figure_factory as ff
from scipy.spatial.distance import squareform, pdist
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.utils import calculate_rmse
from scipy.cluster.hierarchy import linkage, fcluster
import numpy as np


# Shared color and context configuration for 96-context plots
BASES = ['A', 'C', 'G', 'T']
MUTATIONS = ['C>A', 'C>G', 'C>T', 'T>A', 'T>C', 'T>G']
CONTEXTS = [f'{x}[{m}]{y}' for m in MUTATIONS for x in BASES for y in BASES]

COLORS_C = ['blue', 'black', 'red']   # C>A, C>G, C>T
COLORS_T = ['gray', 'green', 'pink']  # T>A, T>C, T>G

BASES_CTX = ['A', 'C', 'G', 'T']
C_CONTEXT_LABELS = [f"{l}C{r}" for l in BASES_CTX for r in BASES_CTX]
T_CONTEXT_LABELS = [f"{l}T{r}" for l in BASES_CTX for r in BASES_CTX]
ALL_CONTEXT_LABELS = C_CONTEXT_LABELS + T_CONTEXT_LABELS

# Short axis labels for 96-context signature plot (same style as reprint: trinucleotide context)
SIGNATURE_X_LABELS = C_CONTEXT_LABELS * 3 + T_CONTEXT_LABELS * 3  # 96 labels matching CONTEXTS order

DENDRO_LINE_COLOR = "#3f3f3f"
# Vertical layout of a clustermap, in paper fractions: matrix, cluster strip,
# top dendrogram. The strip is drawn as paper-referenced shapes rather than its
# own axis, which would collapse and break the render in a short container.
MATRIX_Y1 = 0.82
STRIP_Y0, STRIP_Y1 = 0.828, 0.855
TOP_DENDRO_Y0 = 0.865
# Floor for the rendered figure box. Rotated tick labels claim ~150-190px of
# margin via automargin; below roughly 500px of box the remaining plot area is
# too small for plotly to scale the stacked axes and it aborts the whole render
# ("Something went wrong with axis scaling"), so never hand it a smaller box.
MIN_FIGURE_SIZE = 640
# ColorBrewer 9-class ramps, the ones the published COSMIC+Enviro+KO figures
# use: GnBu for the raw-signature distance matrix, OrRd for the RePrint one.
# Both are applied with reversescale=True, so a distance of 0 is the darkest
# end and the diagonal reads as a dark line, exactly as in the paper.
GNBU_9 = ['#F7FCF0', '#E0F3DB', '#CCEBC5', '#A8DDB5', '#7BCCC4',
          '#4EB3D3', '#2B8CBE', '#0868AC', '#084081']
ORRD_9 = ['#FFF7EC', '#FEE8C8', '#FDD49E', '#FDBB84', '#FC8D59',
          '#EF6548', '#D7301F', '#B30000', '#7F0000']

CLUSTER_STRIP_PALETTE = [
    "#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3",
    "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD",
    "#A1C9F4", "#FFB482", "#8DE5A1", "#FF9F9B", "#D0BBFF",
    "#DEBB9B", "#FAB0E4", "#CFCFCF", "#FFFEA3", "#B9F2F0",
]

# Keep legend styling consistent across all mutation plots.
MUTATION_LEGEND = dict(
    title=dict(text="Mutation Type"),
    x=1.02,
    y=1.0,
    xanchor="left",
    yanchor="top",
    bgcolor="rgba(255,255,255,0.9)",
    bordercolor="rgba(0,0,0,0.2)",
    borderwidth=1,
    font=dict(size=12),
    tracegroupgap=8,
)

def create_main_dashboard(df, signature, title, yaxis_title):
    frequencies = df[signature] * 1

    mutations = MUTATIONS
    contexts = CONTEXTS

    colors = {
        'C>A': COLORS_C[0],
        'C>G': COLORS_C[1],
        'C>T': COLORS_C[2],
        'T>A': COLORS_T[0],
        'T>C': COLORS_T[1],
        'T>G': COLORS_T[2],
    }

    fig = go.Figure()
    
    for mutation in mutations:
        mutation_contexts = [c for c in contexts if f'[{mutation}]' in c]
        mutation_frequencies = [frequencies[mc] if mc in frequencies.index else 0 for mc in mutation_contexts]
        
        fig.add_trace(go.Bar(
            x=mutation_contexts,
            y=mutation_frequencies,
            name=mutation,
            marker_color=colors[mutation]
        ))

    y_max = frequencies.max()

    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center',
            font=dict(size=12),
            y=0.95
        ),
        xaxis_title='Mutation Context',
        yaxis_title=yaxis_title,
        template='plotly_white',
        barmode='group',
        legend=MUTATION_LEGEND,
        yaxis_range=[0, y_max],
        margin=dict(l=50, r=50, t=80, b=150),
        width=1000,
        height=520,
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(96)),
            ticktext=SIGNATURE_X_LABELS,
            tickangle=90,
            tickfont=dict(size=9),
        ),
        yaxis=dict(tickfont=dict(size=10))
    )

    return fig


def _extract_reprint_vector_from_series(series):
    """
    Convert a 96-context RePrint Series into C and T probability matrices.

    Expects index like 'A[C>A]A', 'A[C>A]C', ..., with values as probabilities.
    Returns:
        c_probs: (16, 3) array for C>A, C>G, C>T
        t_probs: (16, 3) array for T>A, T>C, T>G
    """
    c_probs = np.zeros((16, 3))
    t_probs = np.zeros((16, 3))

    bases_list = BASES_CTX

    for idx, value in series.items():
        # idx: L[X>Y]R
        try:
            parts = idx.split('[')
            left_base = parts[0]
            mutation_and_right = parts[1].split(']')
            mutation = mutation_and_right[0]
            right_base = mutation_and_right[1]
        except Exception:
            # Skip malformed indices silently
            continue

        ref_base, mut_base = mutation.split('>')

        left_idx = bases_list.index(left_base)
        right_idx = bases_list.index(right_base)
        context_idx = left_idx * 4 + right_idx

        if ref_base == 'C':
            mut_order = ['A', 'G', 'T']  # C>A, C>G, C>T
            mut_idx = mut_order.index(mut_base)
            c_probs[context_idx, mut_idx] = float(value)
        elif ref_base == 'T':
            mut_order = ['A', 'C', 'G']  # T>A, T>C, T>G
            mut_idx = mut_order.index(mut_base)
            t_probs[context_idx, mut_idx] = float(value)

    return c_probs, t_probs


def create_reprint_footprint_figure(df_reprint, signature, title=None, show_x_labels=True):
    """
    Create a three-panel RePrint footprint figure matching the standalone Plotly script,
    but driven directly from the RePrint DataFrame used in the app.

    df_reprint: DataFrame with 96-context index and RePrint signatures as columns
    signature: column name to plot
    """
    if signature not in df_reprint.columns:
        raise ValueError(f"Signature '{signature}' not found in RePrint data")

    series = df_reprint[signature]
    c_probs, t_probs = _extract_reprint_vector_from_series(series)

    # X positions with a gap
    x_pos_c = np.arange(16)
    x_pos_t = np.arange(16) + 16.5
    x_pos = np.concatenate([x_pos_c, x_pos_t])

    # Tick labels
    if show_x_labels:
        ticktext = ALL_CONTEXT_LABELS
        tickvals = x_pos
    else:
        ticktext, tickvals = [], []

    if title is None:
        title = f"{signature} RePrint"

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.00,
        row_heights=[0.33, 0.34, 0.33],
    )

    width = 0.95

    # Bottom panel (row 3): C>A and T>A from 0 up
    fig.add_trace(
        go.Bar(
            x=x_pos_c, y=c_probs[:, 0],
            width=width, marker=dict(color=COLORS_C[0], line=dict(color="white", width=0.5)),
            name="C>A", legendgroup="C", showlegend=True,
            hovertemplate="Context=%{customdata}<br>Mutation=C>A<br>p=%{y:.4f}<extra></extra>",
            customdata=C_CONTEXT_LABELS,
        ),
        row=3, col=1
    )
    fig.add_trace(
        go.Bar(
            x=x_pos_t, y=t_probs[:, 0],
            width=width, marker=dict(color=COLORS_T[0], line=dict(color="white", width=0.5)),
            name="T>A", legendgroup="T", showlegend=True,
            hovertemplate="Context=%{customdata}<br>Mutation=T>A<br>p=%{y:.4f}<extra></extra>",
            customdata=T_CONTEXT_LABELS,
        ),
        row=3, col=1
    )

    # Middle panel (row 2): centered bars
    c_hm = c_probs[:, 1]
    t_hm = t_probs[:, 1]
    fig.add_trace(
        go.Bar(
            x=x_pos_c,
            y=c_hm,              # geometria jak była
            base=-c_hm / 2,
            width=width,
            marker=dict(color=COLORS_C[1], line=dict(color="white", width=0.5)),
            name="C>G",
            legendgroup="C",
            showlegend=True,
            hovertemplate="Context=%{customdata[0]}<br>Mutation=C>G<br>p=%{customdata[1]:.4f}<extra></extra>",
            customdata=[[C_CONTEXT_LABELS[i], c_hm[i]] for i in range(len(C_CONTEXT_LABELS))],
        ),
        row=2, col=1
    )
    fig.add_trace(
        go.Bar(
            x=x_pos_t, y=t_hm, base=-t_hm / 2,
            width=width, marker=dict(color=COLORS_T[1], line=dict(color="white", width=0.5)),
            name="T>C", legendgroup="T", showlegend=True,
            hovertemplate="Context=%{customdata[0]}<br>Mutation=T>C<br>p=%{customdata[1]:.4f}<extra></extra>",
            customdata=[[T_CONTEXT_LABELS[i], t_hm[i]] for i in range(len(T_CONTEXT_LABELS))],
        ),
        row=2, col=1
    )

    # Top panel (row 1): inverted y-axis
    fig.add_trace(
        go.Bar(
            x=x_pos_c, y=c_probs[:, 2],
            width=width, marker=dict(color=COLORS_C[2], line=dict(color="white", width=0.5)),
            name="C>T", legendgroup="C", showlegend=True,
            hovertemplate="Context=%{customdata}<br>Mutation=C>T<br>p=%{y:.4f}<extra></extra>",
            customdata=C_CONTEXT_LABELS,
        ),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(
            x=x_pos_t, y=t_probs[:, 2],
            width=width, marker=dict(color=COLORS_T[2], line=dict(color="white", width=0.5)),
            name="T>G", legendgroup="T", showlegend=True,
            hovertemplate="Context=%{customdata}<br>Mutation=T>G<br>p=%{y:.4f}<extra></extra>",
            customdata=T_CONTEXT_LABELS,
        ),
        row=1, col=1
    )

    fig.update_layout(
        barmode="overlay",
        title=dict(text=title, x=0.5, y=0.98, xanchor="center", yanchor="top"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=20, r=80, t=60, b=80),
        width=1000,
        height=520,
        legend=MUTATION_LEGEND,
    )

    # X axis (only visible on bottom)
    fig.update_xaxes(
        row=3, col=1,
        tickmode="array",
        tickvals=tickvals,
        ticktext=ticktext,
        tickangle=90,
        showgrid=False,
        zeroline=False,
        showline=False,
        ticks="",
    )
    fig.update_xaxes(row=1, col=1, showticklabels=False)
    fig.update_xaxes(row=2, col=1, showticklabels=False)

    # Remove y axes; set ranges; invert top
    fig.update_yaxes(row=3, col=1, range=[0, 1.0], visible=False)
    fig.update_yaxes(row=2, col=1, range=[-0.5, 0.5], visible=False)
    fig.update_yaxes(row=1, col=1, range=[1.0, 0], visible=False)

    # X limits
    max_x = float(x_pos.max())
    for r in (1, 2, 3):
        fig.update_xaxes(range=[-0.5, max_x + 0.8], row=r, col=1)

    # Scale bar on the right (bottom panel coordinates)
    scale_x = max_x + 1.1
    fig.add_shape(
        type="line",
        x0=scale_x, x1=scale_x, y0=0, y1=1.0,
        xref="x3", yref="y3",
        line=dict(color="black", width=2),
        layer="above",
    )
    # end caps
    fig.add_shape(type="line", x0=scale_x - 0.1, x1=scale_x + 0.1, y0=0, y1=0,
                  xref="x3", yref="y3", line=dict(color="black", width=2), layer="above")
    fig.add_shape(type="line", x0=scale_x - 0.1, x1=scale_x + 0.1, y0=1.0, y1=1.0,
                  xref="x3", yref="y3", line=dict(color="black", width=2), layer="above")

    ticks = [0, 0.25, 0.5, 0.75, 1.0]
    for y in ticks:
        fig.add_shape(
            type="line",
            x0=scale_x - 0.05, x1=scale_x + 0.05, y0=y, y1=y,
            xref="x3", yref="y3",
            line=dict(color="black", width=1.5),
            layer="above",
        )
        fig.add_annotation(
            x=scale_x + 0.3, y=y,
            xref="x3", yref="y3",
            text=str(y),
            showarrow=False,
            xanchor="left",
            yanchor="middle",
            font=dict(size=12, color="black"),
        )

    return fig


def create_heatmap_with_custom_sim(df, calc_func=calculate_rmse, colorscale='Blues', hide_heatmap=False, method='complete', cluster_threshold_frac=0.7, metric_label='Similarity', annotation_groups=None):
    """Clustered distance-matrix heatmap, built the way the RePrint paper's
    figures are.

    annotation_groups: optional [{'name', 'color', 'members': [...]}, ...].
    When given, the strip above the matrix colours each column by the fixed
    group it belongs to (blank for columns in no group) instead of by the
    clusters cut out of this particular dendrogram.
    """
    # Transpose data and get labels
    df = df.T
    labels = df.index.tolist()

    n = df.shape[0]
    if n <= 10:
        px_per_label = 55
        label_font_size = 11
    elif n <= 20:
        px_per_label = 40
        label_font_size = 10
    elif n <= 40:
        px_per_label = 28
        label_font_size = 9
    else:
        px_per_label = 18
        label_font_size = 8

    max_size = max(MIN_FIGURE_SIZE, min(2200, px_per_label * n + 150))
    min_size = max(MIN_FIGURE_SIZE, min(max_size, 13 * n + 160))
    size_meta = {'min_size': min_size, 'max_size': max_size}
    # Feed calc_func plain numpy rows rather than df.iloc slices: same numbers,
    # about ten times faster, which matters at the paper's 102 signatures.
    values = df.to_numpy()
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            rmse = calc_func(df.iloc[i, :], df.iloc[j, :])
            dist_matrix[i, j] = rmse
            dist_matrix[j, i] = rmse

    condensed_rmse = squareform(dist_matrix)
    Z = linkage(condensed_rmse, method=method)

    if hide_heatmap:
        # No heatmap: show a standalone vertical dendrogram (leaves along the
        # bottom, tree growing upward).
        fig = ff.create_dendrogram(df.values, labels=labels, orientation='bottom', linkagefun=lambda _: Z)

        fig.update_layout({'autosize': True, 'meta': size_meta,
                           'showlegend': False, 'hovermode': 'closest',
                           'margin': dict(l=50, r=50, t=60, b=50),
                           })
        fig.update_layout(xaxis={'domain': [0, 1],
                                 'mirror': False,
                                 'showgrid': False,
                                 'showline': False,
                                 'zeroline': False,
                                 'showticklabels': True,
                                 'automargin': True,
                                 })
        fig.update_layout(yaxis={'domain': [0, 1],
                                 'mirror': False,
                                 'showgrid': False,
                                 'showline': False,
                                 'zeroline': False,
                                 'showticklabels': True,
                                 })

        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)")

        fig.update_layout(
            font=dict(size=label_font_size)
        )

        return fig

    # Top dendrogram (leaves at the bottom, root growing up), drawn on y2 above
    # the matrix so the column order is readable as a tree.
    fig = ff.create_dendrogram(df.values, labels=labels, orientation='bottom', linkagefun=lambda _: Z)
    for trace in fig['data']:
        trace['yaxis'] = 'y2'
        trace['line']['color'] = DENDRO_LINE_COLOR
        trace['line']['width'] = 1
        trace['hoverinfo'] = 'skip'

    # Side dendrogram, drawn on x2 to the left of the matrix
    dendro_side = ff.create_dendrogram(df.values, orientation='right', linkagefun=lambda _: Z)
    for trace in dendro_side['data']:
        trace['xaxis'] = 'x2'
        trace['line']['color'] = DENDRO_LINE_COLOR
        trace['line']['width'] = 1
        trace['hoverinfo'] = 'skip'
        fig.add_trace(trace)
    dendro_leaves = dendro_side['layout']['yaxis']['ticktext']
    dendro_leaves = list(map(int, dendro_leaves))

    # Create heatmap
    heat_data = dist_matrix[dendro_leaves, :]
    heat_data = heat_data[:, dendro_leaves]

    cluster_threshold = cluster_threshold_frac * Z[:, 2].max()
    cluster_ids = fcluster(Z, t=cluster_threshold, criterion='distance')
    ordered_cluster_ids = [cluster_ids[leaf] for leaf in dendro_leaves]


    ordered_labels = [labels[leaf] for leaf in dendro_leaves]
    cluster_members = {}
    for cid in set(ordered_cluster_ids):
        members = [lbl for lbl, c in zip(ordered_labels, ordered_cluster_ids) if c == cid]
        cluster_members[cid] = f"<br><br>Cluster ({len(members)} signatures):<br>" + "<br>".join(members) if len(members) > 1 else ""

    group_of = {}
    for group in (annotation_groups or []):
        for member in group['members']:
            group_of[member] = group['name']
    group_notes = [
        f"<br>Group: {group_of[lbl]}" if lbl in group_of else ""
        for lbl in ordered_labels
    ]

    customdata = [
        [
            [col_lbl, row_lbl, cluster_members[row_c] if row_c == col_c else "",
             row_note]
            for col_lbl, col_c in zip(ordered_labels, ordered_cluster_ids)
        ]
        for row_lbl, row_c, row_note in zip(ordered_labels, ordered_cluster_ids, group_notes)
    ]

    heatmap = [
        go.Heatmap(
            x=dendro_leaves,
            y=dendro_leaves,
            z=heat_data,
            reversescale=True,
            colorscale=colorscale,
            colorbar=dict(
                x=0.0, xanchor='left',
                y=1.0, yanchor='top',
                len=0.13, thickness=12,
                title=dict(text=metric_label, side='top'),
                tickfont=dict(size=max(7, label_font_size - 1)),
            ),
            customdata=customdata,
            hovertemplate=(
                '%{customdata[1]} vs %{customdata[0]}%{customdata[3]}'
                f'<br>{metric_label}: %{{z:.3f}}%{{customdata[2]}}<extra></extra>'
            )
        )
    ]

    heatmap[0]['x'] = fig['layout']['xaxis']['tickvals']
    heatmap[0]['y'] = dendro_side['layout']['yaxis']['tickvals']

    # Add heatmap data to the figure
    for data in heatmap:
        fig.add_trace(data)

    x_tickvals = list(heatmap[0]['x'])
    half_dx = (x_tickvals[1] - x_tickvals[0]) / 2 if n > 1 else 5

    if annotation_groups:
        color_by_group = {g['name']: g['color'] for g in annotation_groups}
        strip_colors = [color_by_group.get(group_of.get(lbl)) for lbl in ordered_labels]
    else:
        palette_slot = {}
        strip_colors = []
        cluster_sizes = {cid: ordered_cluster_ids.count(cid) for cid in set(ordered_cluster_ids)}
        for cid in ordered_cluster_ids:
            if cluster_sizes[cid] < 2:
                strip_colors.append(None)
                continue
            if cid not in palette_slot:
                palette_slot[cid] = len(palette_slot)
            strip_colors.append(CLUSTER_STRIP_PALETTE[palette_slot[cid] % len(CLUSTER_STRIP_PALETTE)])

    start = 0
    for i in range(1, n + 1):
        if i == n or strip_colors[i] != strip_colors[start]:
            if strip_colors[start] is not None:
                fig.add_shape(
                    type="rect",
                    x0=x_tickvals[start] - half_dx, x1=x_tickvals[i - 1] + half_dx,
                    y0=STRIP_Y0, y1=STRIP_Y1,
                    xref="x", yref="paper",
                    line=dict(width=0),
                    fillcolor=strip_colors[start],
                    layer="above",
                )
            start = i

    fig.update_layout({'autosize': True, 'meta': size_meta,
                       'showlegend': False, 'hovermode': 'closest',
                       # automargin grows the edges that carry tick labels
                       'margin': dict(l=10, r=10, t=20, b=10),
                       })

    # Matrix columns + bottom labels
    fig.update_layout(xaxis={'domain': [.15, 1],
                            'mirror': False,
                            'showgrid': False,
                            'showline': False,
                            'zeroline': False,
                            'side': 'bottom',
                            'ticks': 'outside',
                            'ticklen': 3,
                            'tickangle': -90,
                            'automargin': True,
                            'tickvals': x_tickvals,
                            'ticktext': ordered_labels,
                            })

    # Side dendrogram x
    fig.update_layout(xaxis2={'domain': [0, .145],
                            'mirror': False,
                            'showgrid': False,
                            'showline': False,
                            'zeroline': False,
                            'showticklabels': False,
                            'ticks': "",
                            })

    # Matrix rows + right labels
    fig.update_layout(yaxis={'domain': [0, MATRIX_Y1],
                             'mirror': False,
                             'showgrid': False,
                             'showline': False,
                             'zeroline': False,
                             'showticklabels': True,
                             'ticks': 'outside',
                             'ticklen': 3,
                             'automargin': True,
                             'tickvals': dendro_side['layout']['yaxis']['tickvals'],
                             'ticktext': ordered_labels,
                             'side': 'right',
                             })

    # Top dendrogram y
    fig.update_layout(yaxis2={'domain': [TOP_DENDRO_Y0, 1],
                              'anchor': 'x',
                              'mirror': False,
                              'showgrid': False,
                              'showline': False,
                              'zeroline': False,
                              'showticklabels': False,
                              'ticks': "",
                              })


    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)")

    fig.update_layout(
        font=dict(size=label_font_size)
    )

    return fig

def create_vertical_dendrogram_with_query_labels_right(df, calc_func=calculate_rmse, method='complete', text=''):
    import pandas as pd
    import plotly.figure_factory as ff
    import plotly.graph_objects as go
    from scipy.spatial.distance import pdist
    from scipy.cluster.hierarchy import linkage

    df = df.T
    df.index = df.index.astype(str)
    ref_df = df[df.index.str.endswith('_ref')]
    query_df = df[df.index.str.endswith('_query')]

    if ref_df.empty:
        return go.Figure().update_layout(title="No _ref signatures available for dendrogram.")

    ref_labels = ref_df.index.tolist()
    query_labels = query_df.index.tolist()

    dist_ref = pdist(ref_df.values, metric=lambda u, v: calc_func(pd.Series(u), pd.Series(v)))
    Z = linkage(dist_ref, method=method)

    similarity_map = {}
    for query_name in query_labels:
        query_vector = query_df.loc[query_name]
        best_match = None
        best_score = float('inf')
        for ref_name in ref_labels:
            score = calc_func(query_vector, ref_df.loc[ref_name])
            if score < best_score:
                best_score = score
                best_match = ref_name
        if best_match not in similarity_map:
            similarity_map[best_match] = []
        similarity_map[best_match].append(query_name)

    fig = ff.create_dendrogram(ref_df.values, labels=ref_labels, orientation='left', linkagefun=lambda _: Z)
    fig.for_each_trace(lambda trace: trace.update(visible=True))

    ordered_refs = fig['layout']['yaxis']['ticktext']
    updated_labels = []
    for ref in ordered_refs:
        ref_display = ref.replace('_ref', '').replace('_query', '')
        if ref in similarity_map:
            queries = similarity_map[ref]
            queries_display = [q.replace('_ref', '').replace('_query', '') for q in queries]
            label = ", ".join(queries_display) + " → " + ref_display
        else:
            label = ref_display
        updated_labels.append(label)

    # Calculate responsive dimensions based on data size
    num_labels = len(updated_labels)
    # Scale height with number of labels: more labels = taller plot
    if num_labels <= 10:
        px_per_label = 40
    elif num_labels <= 30:
        px_per_label = 30
    else:
        px_per_label = 22
    responsive_height = max(400, px_per_label * num_labels)

    # Scale font size with number of labels
    if num_labels <= 15:
        label_font_size = 11
    elif num_labels <= 30:
        label_font_size = 9
    elif num_labels <= 60:
        label_font_size = 7
    else:
        label_font_size = 6

    # Make width responsive to label length
    max_label_len = len(max(updated_labels, key=len)) if updated_labels else 10
    right_margin = min(400, max(150, int(label_font_size * 0.6 * max_label_len)))

    fig.update_layout(
        yaxis=dict(
            ticktext=updated_labels,
            tickvals=fig['layout']['yaxis']['tickvals'],
            tickfont=dict(size=label_font_size),
            tickangle=0
        ),
        height=responsive_height,
        margin=dict(l=50, r=right_margin, t=60, b=40),
        title=dict(
            text=text,
            x=0.5,
            xanchor='center',
            font=dict(size=12),
            y=0.98
        ),
        font=dict(size=label_font_size),
        autosize=True,
        xaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor='lightgray'
        )
    )

    return fig


def create_empty_figure_with_text(text):
    fig = go.Figure()
    fig.update_layout(
        xaxis={'visible': True},
        yaxis={'visible': True},
        annotations=[{
            'text': text,
            'xref': 'paper',
            'yref': 'paper',
            'showarrow': False,
            'font': {'size': 20}
        }]
    )
    return fig