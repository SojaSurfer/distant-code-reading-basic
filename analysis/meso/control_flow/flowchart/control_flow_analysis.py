import pickle
import re
import sys
from numbers import Real
from pathlib import Path
from typing import Self

import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from networkx.drawing.nx_pydot import pydot_layout, to_pydot
from rich import print, traceback

from analysis.meso.control_flow.flowchart.metrics import Metrics
from analysis.meso.control_flow.flowchart.utils import Node, NodeList



traceback.install()

control_flow_cmds = ["RUN", "STOP", "END", "GOSUB", "GOTO", "THEN", "RETURN"]
terminal_cf = ["STOP", "END", "RETURN"]
load_cms = ["LOAD", ]
control_flow_cmds_narrow = ["GOSUB", "GOTO", "RUN"] + terminal_cf

control_flow_regex = re.compile("|".join(control_flow_cmds))


COLOR_MAP = {"M": "tab:green", "S": "tab:blue", "T": "tab:gray", "D": "tab:orange", "E": "tab:purple", "L": "tab:red"}
PYDOT_COLOR_MAP = {
    "E": "#9467bd",  # tab:purple
    "M": "#2ca02c",  # tab:green
    "S": "#1f77b4",  # tab:blue  
    "D": "#ff7f0e",  # tab:orange
    "L": "#d62728",  # tab:red
    "T": "#7f7f7f",  # tab:gray
}


matplotlib.use('TkAgg')  # or 'Qt5Agg' 
plt.ion()

def write_graph(graph:nx.Graph, path: str|Path = "graph.png", *, only_connected: bool = False) -> None:

    if only_connected:
        graph = graph.edge_subgraph(graph.edges)

    pydot_graph = to_pydot(graph)
    pydot_graph.set_rankdir("TB")  # top-to-bottom ("LR" for left-to-right)

    # Set node colors based on the "body" attribute
    for node in pydot_graph.get_nodes():
        node_name = node.get_name().strip('"')  # Remove quotes from node name
        if node_name in graph.nodes:
            body = graph.nodes[node_name].get("prefix")
            color = PYDOT_COLOR_MAP.get(body, "white")
            
            # Set the fill color and style
            node.set_fillcolor(color)
            node.set_style("filled")

    pydot_graph.write_png(path)
    return None


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


def get_prefix(row) -> str:
    if row["token"] == "THEN" or row["conditional"]:
        return "D"
    elif row["token"] in ("GOSUB", "RETURN"):
        return "S"
    elif row["token"] == "LOAD" or "load" in row["token"]:
        return "L"
    elif row["token"] == "END":
        return "T"
    else:
        return "M"


def get_output_file_names(file_df:pd.DataFrame, output_dir:Path) -> tuple[Path, Path, Path]:
    file_name = file_df["name"].values[0]

    plot_path = output_dir / "plots" / f"{file_name}.png"
    graph_path = output_dir / "pickle" / f"{file_name}.pkl"
    metric_path = output_dir / "metrics.xlsx"

    plot_path.parent.mkdir(exist_ok=True)
    graph_path.parent.mkdir(exist_ok=True)

    return plot_path, graph_path, metric_path




class ControlFlowGraph:

    def __init__(self) -> None:
        self.G = nx.DiGraph()
        self.load_string_df = None


    def init_new_graph(self,file_df:pd.DataFrame) -> None:
        self.G = nx.DiGraph()
        self.df = file_df
        self.df = self.df.reset_index(drop=True)

        self.file_lines = self.df["line"].unique()
        self.start_line = int(self.df.iloc[0]["line"])

        self.nodes = NodeList()
        self.node_to_append_later = set()
        self.subroutine_nodes = []
        return None
    

    def create_graph(self, file_df:pd.DataFrame) -> nx.DiGraph:

        self.init_new_graph(file_df)

        load_df = self.df[(self.df["syntax"] == "SL") & (self.df["token"].str.contains("load"))]
        if not load_df.empty:
            if self.load_string_df is not None:  # Better to check for None explicitly
                self.load_string_df = pd.concat([self.load_string_df, load_df], ignore_index=True)
            else:
                self.load_string_df = load_df

        self._create_nodes()

        self._create_edges()
        return self.G

    
    def _create_nodes(self) -> None:
        """Create a df containing all control flow nodes for a file."""

        self._create_nodedf()

        for idx, row in self.nodedf.iterrows():

            line_jumps = self._get_line_jumps(row, idx)

            node_prefix = get_prefix(row)
            name = f"{node_prefix}_{row['line']}"
            attr = row.to_dict() | {"line_jumps": line_jumps}

            node = Node(name, **attr)
            if node.subroutine and not (node.conditional or node.terminal):
                # a plain subroutine needs no node for the jumping to the subroutine. Since it is always terminal
                # it can be connected directly the the last node. Since new nodes might appear later, the
                # subroutine nodes are added last
                self.subroutine_nodes.append(node)

            elif node in self.nodes:
                # two or more line jumps in one line
                self.nodes.add_line_jumps(node)
            else:
                self.nodes.append(node)

            for line_j in line_jumps:
                line_j_row = self.nodedf[self.nodedf["line"] == line_j]
                if line_j_row.empty or self._is_plain_subroutine(line_j_row):
                    # the statement does not jump to an existing node, create it later because in between two existing nodes can be created another node later
                    node_prefix = "S" if attr["subroutine"] else "M"
                    name = f"{node_prefix}_{line_j}"

                    attr = {"line": line_j, "line_jumps": [], "token": None, "conditional": False, "subroutine": attr["subroutine"], "terminal": False}
                    node = Node(name, **attr)
                    if self.file_lines[-1] >= line_j:
                        # do not add the node if the jump is beyond the last line. In this case a terminal node will be added later by self._get_line_jumps
                        self.node_to_append_later.add(node)


        self._add_nodes()
        return None


    def _create_nodedf(self) -> None:
        mask_to_keep = (
            self.df["token"].isin(control_flow_cmds_narrow + load_cms) |
            ((self.df["token"] == "THEN") & 
            self.df["token"].shift(-1).str.isdigit()) |
            ((self.df["syntax"] == "SL") & (self.df["token"].str.contains("load")) & (self.df["token"].shift(-1) == "CHR$")) # catching a print load: PRINT "{down}{down}load" CHR$ ( 34 ), "name"...
        )

        self.nodedf = self.df[mask_to_keep]
        self.nodedf = self.nodedf.drop(columns=["file_id", "game_id", "name", "token_id", "bytes", "syntax", "language"])

        self.nodedf["subroutine"] = (self.nodedf["token"].isin({"GOSUB", "RETURN"}))
        self.nodedf["conditional"] = self.nodedf.apply(self._is_conditional, axis=1)
        self.nodedf["terminal"] = self.nodedf["token"].isin(terminal_cf)

        self.nodedf = self.nodedf[["line", "token", "conditional", "subroutine", "terminal"]]
        return None
    

    def _add_nodes(self) -> None:
        self._add_first_and_last_node()

        self._add_nodes_to_append_later()

        self._add_load_nodes()

        self._add_subroutine_nodes()

        self._add_nodes_to_graph()
        return None
    

    def _add_nodes_to_graph(self) -> None:
        self.nodes.merge_same_line()
        self.nodes.sort()
        self.G = self.nodes.add_to_graph(self.G)
        return None
    

    def _add_load_nodes(self) -> None:
        for node in self.nodes.nodes:
            if node.prefix == "L":
                # LOAD node is unconnected, needs to be connected with the next node
                next_node = (self.nodes > node)[0]
                node.line_jumps.append(next_node.line)
                self.nodes.add_line_jumps(node)
        return None
    

    def _add_subroutine_nodes(self) -> None:
        for node in sorted(self.subroutine_nodes, key=lambda n: n.line):

            if f"M_{node.line}" in self.nodes:
                # sometimes a node is present twice as main and subroutine...
                pass

            last_node = (self.nodes <= node)[-1] # comparison operator return a list of matching nodes based on node.line
            last_node.line_jumps = node.line_jumps + last_node.line_jumps
            self.nodes.add_line_jumps(last_node)
        return None
    

    def _add_nodes_to_append_later(self) -> None:
        node_to_append_later = sorted(self.node_to_append_later, key=lambda n: n.line, reverse=True)
        
        for node in node_to_append_later:

            # next_nodes = self.nodedf[(self.nodedf["line"] > node.line) & (self.nodedf["token"] != "GOSUB")]
            next_nodes = (self.nodes >= node)

            if next_nodes:
                node.line_jumps.append(next_nodes[0].line)

            if node not in self.nodes:
                self.nodes.append(node)
        return None
    

    def _create_edges(self) -> None:
        for node, attrs in sorted(self.G.nodes(data=True), key=lambda ntuple: ntuple[1]["line"]):
            # print(f"{node}: {attrs}")

            if attrs["conditional"] and attrs["token"] == "END":
                # conditional end, node does not exist. Warning: will create nodes with duplicate line number!
                # bad practice...

                end_node_name = f"T_{attrs['line']}"
                attr = {"line": attrs["line"], "line_jumps": [], "token": "END", "conditional": False, "subroutine": attrs["subroutine"], "terminal": True}
                end_node = Node(end_node_name, **attr)
                self.G = self.nodes.add_to_graph(self.G, [end_node])
                self.G.add_edge(node, end_node.name)

            for lj in attrs["line_jumps"]:
                try:
                    child_node = self.nodes[lj]
                except IndexError:
                    raise
                self.G.add_edge(node, child_node.name)

        return None


    def _add_first_and_last_node(self) -> None:
        
        first_line = self.file_lines[0]
        attr = {"line": first_line, "line_jumps": [], "token": None, "conditional": False, "subroutine": False, "terminal": False}

        if first_line in self.nodedf["line"].to_numpy():
            try:
                node = self.nodes[first_line]
            except IndexError:
                # first node is a line_jump node but was not created yet. Should be because it starts a subroutine
                node = [x for x in self.subroutine_nodes if str(first_line)][0]
                self.subroutine_nodes.remove(node)

            attr = {"line": first_line, "line_jumps": node.line_jumps, "token": node.token, "conditional": node.conditional, 
                    "subroutine": node.subroutine, "terminal": node.terminal}
            
        name = f"E_{first_line}"
        node = Node(name, **attr)
        self.node_to_append_later.add(node)

        # remove an existing first-line node with wrong prefix
        nodes_to_remove = {n for n in self.node_to_append_later if n.line == first_line and n.name != name}
        for n in nodes_to_remove:
            self.node_to_append_later.remove(n)


        last_line = self.file_lines[-1]
        if last_line not in self.nodedf["line"].to_numpy():
            name = f"T_{last_line}"

            attr = {"line": last_line, "line_jumps": [], "token": None, "conditional": False, "subroutine": False, "terminal": True}
            node = Node(name, **attr)
            self.nodes.append(node)

        return None


    def _is_conditional(self, row:pd.Series) -> bool:
        if row["token"] == "THEN":
            return True
        
        line_df = self.df[(self.df["line"] == row["line"]) & (self.df.index <= row.name)]

        # possible conditionals are IF cond THEN JUMP_EXPRESSION xxx, IF cond THEN expression : JUMP_EXPRESSION xxx, IF cond JUMP_EXPRESSION xxx
        return (line_df["token"] == "IF").any()
    

    def _is_plain_subroutine(self, rows:pd.DataFrame) -> bool:
        """Check if a line jump is done to a plain GOSUB statement line."""

        row = rows.iloc[0]
        return row["subroutine"] and not (row["terminal"] or row["conditional"])
    

    def _is_terminal_subroutine(self, rows:pd.DataFrame) -> None:
        
        row = rows.iloc[0]
        return row["subroutine"] and row["terminal"]
    

    def _peek_next_line_token(self, idx:Real, row:pd.Series) -> str:

        if len(self.df) <= idx+1:
            return ""
        
        next_row = self.df.iloc[idx+1]
        next_line = int(next_row["line"])

        next_token = "" if next_line != row["line"] else next_row["token"]
        return next_token
    

    def _get_line_jumps(self, row:pd.Series, idx:Real) -> list[int]:
        line_jumps = []

        next_token = self._peek_next_line_token(idx, row)

        match row["token"]:
            case "RUN":
                jump = int(next_token) if next_token else self.start_line
                line_jumps.append(jump)
            case "GOTO":
                jump = int(next_token) if next_token else 0
                line_jumps.append(jump)
            case "GOSUB":
                line_jumps.extend(self._get_gosub_linejumps(row, idx, next_token))
            case "THEN":
                line_jumps.append(int(next_token))
            case "LOAD":
                # load a file
                pass
            case "STOP" | "END":
                # end of file
                pass
            case "RETURN":
                # end of subroutine
                pass
            case _:
                # a print load command which is tagged just as string
                pass  # raise ValueError((row["token"], next_token))


        if row["conditional"]:
            next_line_idx = np.where(self.file_lines == row["line"])[0][0] + 1

            if len(self.file_lines) > next_line_idx:
                next_line = self.file_lines[next_line_idx]
            else:
                # cond=False line does not exist. This happens if a conditional jump is the last line of the program.
                # We add a terminal node at the next line for clarifications
                next_line = self.file_lines[-1] + 1

                name = f"T_{next_line}"

                attr = {"line": next_line, "line_jumps": [], "token": None, "conditional": False, "subroutine": row["subroutine"], "terminal": True}
                node = Node(name, **attr)
                self.node_to_append_later.add(node)


            # only for cond=True??
            # if not self._line_jump_in_same_line(row, idx): 
            line_jumps.append(next_line)
        
        return line_jumps


    def _get_gosub_linejumps(self, row:pd.Series, idx:Real, next_token:str) -> list[int]:
        line_jumps = []
        while next_token:
            if next_token.isdigit():
                line_jumps.append(int(next_token))
            elif next_token != ",":
                break

            idx += 1
            next_token = self._peek_next_line_token(idx, row)

        #   310 FOR t = 2 TO x : ON t GOSUB , 3020 , 3040 , 3070 , 3090 , 3110 , 3150 , 3190 , 3220 : NEXT
        return line_jumps
    

    def _line_jump_in_same_line(self, row:pd.Series, idx:int) -> bool:

        # a df with all line jump statements appearing in the same row after the current line jump statement
        following = self.nodedf[(self.nodedf["line"] == row["line"]) & (self.nodedf.index > idx)]
        preceding = self.nodedf[(self.nodedf["line"] == row["line"]) & (self.nodedf.index < idx)]

        # either there are no other line jump cmds in the line or there is a previous line jump cmd in the row
        same_line_line_jumps = not following.empty and preceding.empty

        # if all line jumps are subroutine, the next line will be reached nevertheless
        return same_line_line_jumps and not (following["token"] == "GOSUB").all()
    

    def save_graph(self, path:str|Path) -> None:
        with open(path, "wb") as file:
            pickle.dump(self.G, file)
        return None
    


if __name__ == "__main__":
    # problems: star-wars2: duplicate filenames but create duplicate graphs...

    path = "/Users/julian/Documents/3 - Bildung/31 - Studium/314 Universität Stuttgart/314.2 Semester 2/Projektarbeit/corpus/dataset/tokenized_dataset.parquet"
    output_dir = Path("analysis/meso/control_flow/flowchart")
    
    df = pd.read_parquet(path)
    CREATE_NEW_PLOTS = False

    cfg = ControlFlowGraph()
    metrics = Metrics()


    for game_id in df["game_id"].unique():
        game_df: pd.DataFrame = df[df["game_id"] == game_id]
        game_graphs = []
        line_count = 0

        for file in game_df["file_id"].unique():
            file_df: pd.DataFrame = game_df[game_df["file_id"] == file]

            file_df = file_df.drop_duplicates() # why are there duplicates?
            plot_path, graph_path, metric_path = get_output_file_names(file_df, output_dir)
            print(plot_path.stem)


            graph = cfg.create_graph(file_df)
            if CREATE_NEW_PLOTS:
                write_graph(graph, plot_path)
                cfg.save_graph(graph_path)
                # show_graph(graph)

            game_graphs.append(graph)
            line_count += len(cfg.file_lines)


        metrics.calculate(game_graphs, line_count, game_df)
        # metrics.print_metrics()


    metrics.save_df(metric_path)
