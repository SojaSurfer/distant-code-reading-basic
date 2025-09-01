from pathlib import Path
from typing import Any, Callable, Literal

import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from networkx.drawing.nx_pydot import pydot_layout



COLOR_MAP = {"M": "tab:green", "S": "tab:blue", "T": "tab:gray", "D": "tab:orange", "E": "tab:purple", "L": "tab:red"}
PYDOT_COLOR_MAP = {
    "M": "#2ca02c",  # tab:green
    "S": "#1f77b4",  # tab:blue  
    "T": "#7f7f7f",  # tab:gray
    "D": "#ff7f0e",  # tab:orange
    "E": "#9467bd",  # tab:purple
    "L": "#d62728"   # tab:red
}


matplotlib.use('TkAgg')  # or 'Qt5Agg' 
plt.ion()

def show_graph(graph:nx.Graph, *, only_connected: bool = False) -> None:

    if only_connected:
        graph = graph.edge_subgraph(graph.edges)

    node_colors = [PYDOT_COLOR_MAP.get(node[0], "white") if isinstance(node, str) else PYDOT_COLOR_MAP.get(node.prefix, "white") for node in graph.nodes()]

    # Create hierarchical layout using pydot
    pos = pydot_layout(graph, prog="dot")

    nx.draw_networkx(graph, pos, with_labels=True, node_size=1000, node_color=node_colors)
    plt.tight_layout()
    plt.show(block=True)
    plt.close()
    return None


class Metrics:

    def __init__(self) -> None:
        self.G: nx.DiGraph = None
        self.metrics: dict[str, Any] = {}
        self.df = pd.DataFrame()
        self.prefixes = ("M", "S", "T", "D", "E", "L")
        return None
    
    
    def calculate(self, graphs:list[nx.DiGraph], line_count:int, game_df:pd.DataFrame) -> dict[str, Any]:
        
        self.G = self._merge_graphs(graphs)

        m = self.metrics = game_df[["game_id", "name"]].iloc[0].to_dict()
        m["lines"] = line_count
        m["files"] = len(graphs)

        m["nodes"] = self.G.number_of_nodes()
        m["edges"] = self.G.number_of_edges()
        for prefix in self.prefixes:
            m[f"nodes_{prefix}"] = len([n for n in self.G.nodes if n.startswith(prefix)])
            m[f"nodes_{prefix}_rel"] = m[f"nodes_{prefix}"] / m["nodes"]

        m["node_coverage"] = m["nodes"] / line_count
            
        m["node_connectivity"] = nx.node_connectivity(self.G)
        m["edge_connectivity"] = nx.edge_connectivity(self.G)


        m["transitivity"] = nx.transitivity(self.G)
        m["density"] = nx.density(self.G)

        deg_dict = dict(self.G.degree)
        m["max_degree"] = max(deg_dict.values())
        m["avg_degree"] = sum(deg_dict.values()) / m["nodes"]

        m["independent_cycles"] = len(nx.minimum_cycle_basis(self.G.to_undirected()))
        p = nx.number_connected_components(self.G.to_undirected())
        m["cyclomatic_complexity"] = m["edges"] - m["nodes"] + 2 * p
        m["weakly_components"] = p  # weakly connected components

        # NP-hard problem, take too long
        # cycles = list(nx.simple_cycles(self.G))
        # lengths = [len(cycle) for cycle in cycles]
        # m["longest_cycle"] = max(lengths)
        # m["shortest_cycle"] = min(lengths)
        
        m["longest_cycle"] = None
        m["shortest_cycle"] = None

        self._calculate_centrality(nx.degree_centrality)
        self._calculate_centrality(nx.in_degree_centrality)
        self._calculate_centrality(nx.out_degree_centrality)
        self._calculate_centrality(nx.betweenness_centrality)
        self._calculate_centrality(nx.closeness_centrality)
        self._calculate_centrality(nx.harmonic_centrality)
        self._calculate_centrality(nx.katz_centrality)
        self._calculate_centrality(nx.edge_betweenness_centrality)
        self._calculate_centrality(nx.pagerank)
        self._calculate_centrality(nx.eigenvector_centrality, max_iter=1000, tol=1e-06)
        # self._calculate_centrality(nx.clustering)

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
    

    def _merge_graphs(self, graphs:list[nx.DiGraph]) -> nx.DiGraph:
        # in all games, the smaller graph loads the larger graph. Some games to not load their content "l0" instead of "load"
        
        def rename(g:nx.DiGraph, i:int) -> nx.DiGraph:
            mapping =  {name: f"{name}_sub{i}" for name in g.nodes()}
            return nx.relabel_nodes(g, mapping)
        
        def get_entry_node(g: nx.DiGraph) -> str:
            """Get the first entry node (E_) from a graph."""
            entry_nodes = [n for n in g.nodes() if n.startswith("E")]
            return entry_nodes[0] if entry_nodes else list(g.nodes())[0]


        if len(graphs) == 1:
            return graphs[0]
        
        # add the smaller CFG into the biggest file, can be 0,1 or 2
        graph, *other_graphs = sorted(graphs, key=lambda g: g.number_of_nodes())

        load_nodes = [n for n in graph.nodes if n.startswith("L")]

        if load_nodes:
            if len(load_nodes) >= len(other_graphs):
                # the smaller graph loads all other files/graphs
                for i, (l_node, subgraph) in enumerate(zip(load_nodes, other_graphs)):
                    subgraph = rename(subgraph, i)
                    graph = nx.compose(graph, subgraph)
                    graph.add_edge(l_node, get_entry_node(subgraph))

            else:
                # first merge other_graphs
                subgraph1 = rename(other_graphs[0], i=0)
                subgraph2 = rename(other_graphs[1], i=1)
                load_nodes_ = [n for n in subgraph1.nodes if n.startswith("L")]

                subgraph = nx.compose(subgraph1, subgraph2)
                if load_nodes_:
                    subgraph.add_edge(load_nodes_[0], get_entry_node(subgraph2))
                    entry_node = get_entry_node(subgraph1)
                else:
                    # maybe the third graph loads the second
                    load_nodes_ = [n for n in subgraph2.nodes if n.startswith("L")]
                    if load_nodes_:
                        subgraph.add_edge(load_nodes_[0], get_entry_node(subgraph1))
                        entry_node = get_entry_node(subgraph2)


                # now merge the main graph with the merged subgraph
                graph = nx.compose(graph, subgraph)
                graph.add_edge(load_nodes[0], entry_node)

        else:
            # assumtion: no load nodes in any graph. Just at them to one graph without connection
            for i, subgraph in enumerate(other_graphs):
                subgraph = rename(subgraph, i)
                graph = nx.compose(graph, subgraph)


        return graph

