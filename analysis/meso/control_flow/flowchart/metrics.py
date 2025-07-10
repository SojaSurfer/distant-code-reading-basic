from pathlib import Path
from typing import Any, Callable, Literal

import networkx as nx
import pandas as pd



class Metrics:

    def __init__(self) -> None:
        self.G: nx.DiGraph = None
        self.metrics: dict[str, Any] = {}
        self.df = pd.DataFrame()
        self.prefixes = ("M", "S", "T", "D", "E", "L")
        return None
    
    
    def calculate(self, graph:nx.DiGraph, line_count:int, file_df:pd.DataFrame) -> dict[str, Any]:
        
        self.G = graph
        m = self.metrics = file_df[["file_id", "game_id", "name"]].iloc[0].to_dict()

        # maybe calculate some metrics only on the strongly connected components
        # comp = max(nx.strongly_connected_components(self.G), key=len)
        # comp

        m["nodes"] = self.G.number_of_nodes()
        m["edges"] = self.G.number_of_edges()
        for prefix in self.prefixes:
            m[f"nodes_{prefix}"] = len([n for n in self.G.nodes if n.startswith(prefix)])

        m["node_coverage"] = m["nodes"] / line_count
        try:
            m["radius"] = nx.radius(self.G)
            m["average_shortest_path_length"] = nx.average_shortest_path_length(self.G)
            m["diameter"] = nx.diameter(self.G)
        except:
            m["radius"] = None
            m["average_shortest_path_length"] = None
            m["diameter"] = None
            
        m["node_connectivity"] = nx.node_connectivity(self.G)
        try:
            m["edge_connectivity"] = nx.edge_connectivity(self.G)
        except:
            m["edge_connectivity"] = None

        m["transitivity"] = nx.transitivity(self.G)
        m["density"] = nx.density(self.G)

        deg_dict = dict(self.G.degree)
        m["max_degree"] = max(deg_dict.values())
        m["avg_degree"] = sum(deg_dict.values()) / m["nodes"]

        self._calculate_centrality(nx.degree_centrality)
        self._calculate_centrality(nx.betweenness_centrality)
        self._calculate_centrality(nx.closeness_centrality)
        self._calculate_centrality(nx.harmonic_centrality)
        self._calculate_centrality(nx.katz_centrality)
        self._calculate_centrality(nx.edge_betweenness_centrality)
        self._calculate_centrality(nx.pagerank)
        self._calculate_centrality(nx.eigenvector_centrality, max_iter=1000, tol=1e-06)
        self._calculate_centrality(nx.clustering)

        self._update_df()
        return m
    

    def _calculate_centrality(self, centrality_func:Callable[[nx.DiGraph], dict[str, float]], **kwargs) -> None:
        func_name = centrality_func.__name__

        try:
            centrality = centrality_func(self.G, **kwargs)
            max_key = max(centrality, key=centrality.get)
            
            self.metrics[f"{func_name}_max_node"] = max_key
            self.metrics[f"{func_name}_max_value"] = centrality[max_key]
            self.metrics[f"{func_name}_avg_value"] = sum(centrality.values()) / len(centrality)
        except:
            self.metrics[f"{func_name}_max_node"] = None
            self.metrics[f"{func_name}_max_value"] = None
            self.metrics[f"{func_name}_avg_value"] = None
        
        return None
    
    def _update_df(self) -> None:
        metrics_row = pd.DataFrame([self.metrics])  # Note the list wrapper
        
        if self.df.empty:
            self.df = metrics_row
        else:
            self.df = pd.concat([self.df, metrics_row], ignore_index=True)
        return None
    

    def print_metrics(self, method:Literal["max", "average"] = "max") -> None:
        for metric_name, value in self.metrics.items():
            if isinstance(value, dict):
                if method == "max":
                    # Find the key with the maximum value
                    max_key = max(value, key=value.get)
                    print(f"{metric_name} (max): {max_key} = {value[max_key]}")
                elif method == "average":
                    # Calculate average of all values
                    avg_value = sum(value.values()) / len(value) if value else 0
                    print(f"{metric_name} (avg): {avg_value:.4f}")
            else:
                # For non-dict values, just print as-is
                print(f"{metric_name}: {value}")
        return None
    

    def save_df(self, path:Path) -> None:
        self.df.to_excel(path, index=False)
        return None
    