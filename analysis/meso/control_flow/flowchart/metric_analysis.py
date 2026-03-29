import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import plotly.io as pio
pio.templates.default = "ggplot2"


if __name__ == "__main__":
    path = "analysis/meso/control_flow/flowchart/metrics.xlsx"
    outpath = "analysis/meso/control_flow/flowchart/correlation_matrix3.png"
    df = pd.read_excel(path)

    df = df.rename(columns={
        'nodes_M': 'M-Knoten abs',
        'nodes_D': 'D-Knoten abs',
        'nodes_S': 'S-Knoten abs',
        'nodes_T': 'T-Knoten abs',
        'nodes_L': 'L-Knoten abs',
        'nodes_M_rel': 'M-Knoten rel',
        'nodes_D_rel': 'D-Knoten rel',
        'nodes_S_rel': 'S-Knoten rel',
        'nodes_T_rel': 'T-Knoten rel',
        'nodes_L_rel': 'L-Knoten rel',
        'files': "Dateien",
        'lines': 'Zeilen',
        'nodes': 'Knoten',
        'edges': 'Kanten',
        'density': 'Dichte',
        'avg_degree': "Durchschn. Grad",
        'max_degree': "Max. Grad",
        "cyclomatic_complexity": "Cyclomatic Complexity",
    })

    numeric_df = df[[
        'Dateien', 'Zeilen', 'Knoten', 'Kanten', 
        'M-Knoten abs', 'D-Knoten abs', 'S-Knoten abs', 'T-Knoten abs', 'L-Knoten abs',
        'M-Knoten rel', 'D-Knoten rel', 'S-Knoten rel', 'T-Knoten rel', 'L-Knoten rel',

        'Dichte', 'Durchschn. Grad', "Max. Grad", "Cyclomatic Complexity"
        # 'nodes_E', 'nodes_E_rel', -> don't need it: "files" correlates 100%, i.e. one Entry Node per file
        
        # 'node_coverage', 'node_connectivity',
        # 'transitivity', 'density', 'max_degree',  # 'edge_connectivity' is always 0
        # 'avg_degree', 'independent_cycles', 'cyclomatic_complexity',
        # 'weakly_components', 'longest_cycle', 'shortest_cycle',

        # 'degree_centrality_max_value', 'degree_centrality_avg_value',
        # 'in_degree_centrality_max_value', 'in_degree_centrality_avg_value',
        # 'out_degree_centrality_max_value', 'out_degree_centrality_avg_value',
        # 'betweenness_centrality_max_value', 'betweenness_centrality_avg_value',
        # 'closeness_centrality_max_value', 'closeness_centrality_avg_value',
        # 'harmonic_centrality_max_value', 'harmonic_centrality_avg_value',
        # 'katz_centrality_max_value', 'katz_centrality_avg_value',
        # 'edge_betweenness_centrality_max_value', 'edge_betweenness_centrality_avg_value',
        # 'pagerank_max_value', 'pagerank_avg_value',
        # 'eigenvector_centrality_max_value', 'eigenvector_centrality_avg_value',
        ]]
    
    df_corr = numeric_df.corr(method="pearson")

    fig = go.Figure()
    fig.add_trace(
        go.Heatmap(
            x = df_corr.columns,
            y = df_corr.index,
            z = np.array(df_corr),
            text=df_corr.values,
            texttemplate='%{text:.2f}',
            colorscale=[ 
                [0.0, px.colors.qualitative.Dark2[1]],
                [0.99, px.colors.qualitative.Dark2[2]],
                [1.0, px.colors.qualitative.Dark2[0]],
            ]
        )
    )

    fig.update_layout(
        template="ggplot2",
        font=dict(
            family="sans-serif",
            size=12,
        )
    )
    # fig.show()
    fig.write_image(outpath, width=1000, height=1000, scale=2)
