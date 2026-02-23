# Wczytanie danych
import pandas as pd
import numpy as np
from scipy.spatial.distance import pdist, squareform
from scipy.cluster.hierarchy import linkage, dendrogram
import plotly.graph_objects as go

# Załadowanie danych
data = pd.read_csv('COSMIC_v2_SBS_GRCh37.txt', sep='\t')

# Przygotowanie danych do analizy klastrowej
distance_matrix = pdist(data.values.T, 'euclidean')
distance_square_matrix = squareform(distance_matrix)
linked = linkage(distance_matrix, 'ward')

# Etykiety na potrzeby dendrogramu
labels = data.columns.tolist()

# Tworzenie dendrogramów dla osi X i Y
dendro = dendrogram(linked, labels=labels, no_plot=True)
order = dendro['leaves']  # Kolejność indeksów z dendrogramu

# Sortowanie danych zgodnie z klastrowaniem
sorted_data = data.values[order, :]
sorted_data = sorted_data[:, order]

# Tworzenie figury Plotly z heatmapą
fig = go.Figure(data=go.Heatmap(
    z=sorted_data,
    x=[labels[i] for i in order],
    y=[labels[i] for i in order],
    colorscale='Viridis'
))

# Dodanie dendrogramu do layoutu wykresu
fig.update_layout(
    width=800,
    height=800,
    xaxis=dict(tickmode='array', tickvals=np.arange(len(labels)), ticktext=[labels[i] for i in order]),
    yaxis=dict(tickmode='array', tickvals=np.arange(len(labels)), ticktext=[labels[i] for i in order])
)

fig.show()
