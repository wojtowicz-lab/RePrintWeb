import plotly.figure_factory as ff
from scipy.spatial.distance import squareform
import plotly.graph_objects as go
from utils.utils import calculate_rmse
from scipy.cluster.hierarchy import linkage
import numpy as np

def create_main_dashboard(df, signature, title, yaxis_title):
    frequencies = df[signature] * 1

    mutations = ['C>A', 'C>G', 'C>T', 'T>A', 'T>C', 'T>G']
    bases = ['A', 'C', 'G', 'T']
    contexts = [f'{x}[{m}]{y}' for m in mutations for x in bases for y in bases]

    colors = {
        'C>A': 'blue',
        'C>G': 'black',
        'C>T': 'red',
        'T>A': 'gray',
        'T>C': 'green',
        'T>G': 'pink'
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
        title=title,
        xaxis_title='Mutation Context',
        yaxis_title=yaxis_title,
        xaxis_tickangle=-90,
        template='plotly_white',
        barmode='group',
        legend_title='Mutation Type',
        yaxis_range=[0, y_max], 
        margin=dict(l=50, r=50, t=50, b=150),
        xaxis=dict(tickfont=dict(size=8)),
        yaxis=dict(tickfont=dict(size=10))
    )

    return fig


def create_heatmap_with_custom_sim(df, calc_func=calculate_rmse, colorscale='Blues', hide_heatmap=False, method='complete'):
    # Transpose data and get labels
    df = df.T
    labels = df.index.tolist()

    n = df.shape[0]
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            rmse = calc_func(df.iloc[i, :], df.iloc[j, :])
            dist_matrix[i, j] = rmse
            dist_matrix[j, i] = rmse

    condensed_rmse = squareform(dist_matrix)
    Z = linkage(condensed_rmse, method=method)

    # Create bottom dendrogram
    fig = ff.create_dendrogram(df.values, labels=labels, orientation='bottom', linkagefun=lambda _: Z)
    fig.for_each_trace(lambda trace: trace.update(visible=False))

    # Create side dendrogram
    dendro_side = ff.create_dendrogram(df.values, orientation='right', linkagefun=lambda _: Z)
    if not hide_heatmap:
        for i in range(len(dendro_side['data'])):
            dendro_side['data'][i]['xaxis'] = 'x2'
    
    # Add side dendrogram data to the figure
    for data in dendro_side['data']:
        fig.add_trace(data)
    dendro_leaves = dendro_side['layout']['yaxis']['ticktext']
    dendro_leaves = list(map(int, dendro_leaves))
    
    if not hide_heatmap:
        # Create heatmap
        heat_data = dist_matrix[dendro_leaves, :]
        heat_data = heat_data[:, dendro_leaves]

        heatmap = [
            go.Heatmap(
                x=dendro_leaves,
                y=dendro_leaves,
                z=heat_data,
                reversescale=True,
                colorscale=colorscale,
                colorbar=dict(
                    x=1.2,
                    xpad=10
                ),
                hovertemplate='x: %{x}<br>y: %{y}<br>similarity: %{z:.3f}<extra></extra>'
            )
        ]

        heatmap[0]['x'] = fig['layout']['xaxis']['tickvals']
        heatmap[0]['y'] = dendro_side['layout']['yaxis']['tickvals']

        # Add heatmap data to the figure
        for data in heatmap:
            fig.add_trace(data)

        fig.update_layout(xaxis={'domain': [.15, 1],
                                'mirror': False,
                                'showgrid': False,
                                'showline': False,
                                'zeroline': False,
                                'side': 'top',  # Ustawienie etykiet osi X na górze
                                'tickvals': fig['layout']['xaxis']['tickvals'],
                                'ticktext': [labels[i] for i in dendro_leaves]
                                })

        fig.update_layout(xaxis2={'domain': [0, .15],
                                'mirror': False,
                                'showgrid': False,
                                'showline': False,
                                'zeroline': False,
                                'showticklabels': False,
                                })

    fig.update_layout({'width': 700, 'height': 700,
                       'showlegend': False, 'hovermode': 'closest',
                       })
    fig.update_layout(yaxis={'domain': [0, 1],
                             'mirror': False,
                             'showgrid': False,
                             'showline': False,
                             'zeroline': False,
                             'showticklabels': True,
                             'tickvals': dendro_side['layout']['yaxis']['tickvals'],
                             'ticktext': [labels[i] for i in dendro_leaves],
                             'side': 'right',
                             })

    fig.update_layout(yaxis2={'domain': [.825, .975],
                              'mirror': False,
                              'showgrid': False,
                              'showline': False,
                              'zeroline': False,
                              'showticklabels': True,  
                              'ticks': "",
                              })

    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)")

    fig.update_layout(
        font=dict(size=8)
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
        if ref in similarity_map:
            queries = similarity_map[ref]
            label = ", ".join(queries) + " → " + ref
        else:
            label = ref
        updated_labels.append(label)

    # Calculate responsive dimensions
    num_labels = len(updated_labels)
    min_height = max(400, 25 * num_labels)  # Reduced from 30 to 25 per label
    max_height = min(800, min_height)  # Cap maximum height
    
    # Make width responsive and ensure it fits within the card
    responsive_width = min(1000, max(600, 15 * len(max(updated_labels, key=len))))
    
    fig.update_layout(
        yaxis=dict(
            ticktext=updated_labels,
            tickvals=fig['layout']['yaxis']['tickvals'],
            tickfont=dict(size=9),  # Reduced font size
            tickangle=0
        ),
        width=responsive_width,
        height=max_height,
        margin=dict(l=50, r=200, t=40, b=40),  # Reduced right margin
        title=dict(
            text=text,
            x=0.5,
            xanchor='center',
            font=dict(size=14)  # Reduced title font size
        ),
        font=dict(size=9),  # Reduced general font size
        autosize=True,  # Enable autosize
        # Ensure the plot fits within its container
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