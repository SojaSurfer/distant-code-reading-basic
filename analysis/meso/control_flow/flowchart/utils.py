from collections import Counter
from numbers import Real

import networkx as nx



class Node:

    def __init__(self, name:str, line:int, line_jumps:list[int], token:str, conditional:bool, subroutine:bool, terminal:bool) -> None:
        self.name = name
        self.prefix = name[0]
        self.line = line
        self.line_jumps = line_jumps
        self.token = token
        self.conditional = conditional
        self.subroutine = subroutine
        self.terminal = terminal

        assert int(self.name.split("_")[1]) == self.line
        return None

    def __str__(self) -> str:
        return f"{self.__class__.__qualname__}(name={self.name})"

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}(name={self.name!r})"
    


class NodeList:

    def __init__(self, nodes:list[Node] = None) -> None:
        self.nodes = nodes if nodes else []
        return None
    
    def __len__(self) -> int:
        return len(self.nodes)
    
    def __str__(self) -> str:
        return str(self.nodes)
    
    def __repr__(self) -> str:
        
        return repr(self.nodes)
    
    def __contains__(self, other:Node|str|int) -> bool:
        
        if isinstance(other, Node):
            return other.name in [n.name for n in self.nodes]
        elif isinstance(other, str):
            return other in [n.name for n in self.nodes]
        elif isinstance(other, Real):
            return other in [n.line for n in self.nodes]
        else:
            raise TypeError

    def __getitem__(self, other:str|Real|Node) -> Node:
        if isinstance(other, str):
            for n in self.nodes:
                if n.name == other:
                    return n
        
        elif isinstance(other, Real):
            for n in self.nodes:
                if n.line == other:
                    return n

        elif isinstance(other, Node):
            for n in self.nodes:
                if n.name == other.name:
                    return n

        else:
            raise TypeError

        raise IndexError
    
    def __gt__(self, other:Node) -> list[Node]:
        self.sort() # bad practice, do sorting when adding nodes
        if not isinstance(other, Node):
            raise TypeError
        
        return [n for n in self.nodes if n.line > other.line]

    def __lt__(self, other:Node) -> list[Node]:
        self.sort() # bad practice, do sorting when adding nodes
        if not isinstance(other, Node):
            raise TypeError
        
        return [n for n in self.nodes if n.line < other.line]
    
    def __ge__(self, other:Node) -> list[Node]:
        self.sort() # bad practice, do sorting when adding nodes
        if not isinstance(other, Node):
            raise TypeError
        
        return [n for n in self.nodes if n.line >= other.line]

    def __le__(self, other:Node) -> list[Node]:
        self.sort() # bad practice, do sorting when adding nodes
        if not isinstance(other, Node):
            raise TypeError
        
        return [n for n in self.nodes if n.line <= other.line]
    

    def append(self, node:Node) -> None:
        self.nodes.append(node)
        return None


    def remove(self, node) -> None:
        if isinstance(node, Node):
            # Remove by Node object
            self.nodes.remove(node)
        elif isinstance(node, str):
            # Remove by name
            for i, n in enumerate(self.nodes):
                if n.name == node:
                    self.nodes.pop(i)
                    return
            
            msg = f"Node with name '{node}' not found"
            raise ValueError(msg)
        elif isinstance(node, Real):
            # Remove by line number
            for i, n in enumerate(self.nodes):
                if n.line == node:
                    self.nodes.pop(i)
                    return
            
            msg = f"Node with line {node} not found"
            raise ValueError(msg)
        else:
            msg = f"Cannot remove node of type {type(node)}"
            raise TypeError(msg)
        
        return None
    

    def add_line_jumps(self, node:Node) -> None:
        """Search for the node name and add the line jump values of the parameter node to the internal node."""

        n = self.__getitem__(node)
        for lj in node.line_jumps:
            if lj not in n.line_jumps:
                if n.conditional:
                    # multiple line jumps in a conditional statement. Add the following line jumps between the cond=False line continuation
                    n.line_jumps.insert(-1, lj)
                else:
                    n.line_jumps.append(lj)

        return None
    

    def sort(self, reverse: bool = False) -> list[Node]:
        self.nodes = sorted(self.nodes, key=lambda n: int(n.name.split("_")[1]), reverse=reverse)
        return self.nodes
    

    def add_to_graph(self, graph:nx.DiGraph, nodes:list[Node] = None) -> nx.DiGraph:
        if nodes is None:
            for node in self.nodes:
                attr = {"prefix": node.prefix, "line": node.line, "line_jumps": node.line_jumps, "token": node.token,
                        "conditional": node.conditional, "subroutine": node.subroutine, "terminal": node.terminal}
                graph.add_node(node.name, **attr)

        else:
            for node in nodes:
                attr = {"prefix": node.prefix, "line": node.line, "line_jumps": node.line_jumps, "token": node.token,
                        "conditional": node.conditional, "subroutine": node.subroutine, "terminal": node.terminal}
                graph.add_node(node.name, **attr)
                self.append(node)
            
        return graph
    

    def merge_same_line(self) -> None:
        line_counts = Counter(node.line for node in self.nodes)
        duplicate_lines = {line for line, count in line_counts.items() if count > 1}

        for line in duplicate_lines:
            duplicates = sorted([n for n in self.nodes if n.line == line], key=lambda x: x.subroutine) # assumption is that one must be a subroutine 

            if len(duplicates) == 2:
                main, subroutine = duplicates

                for lj in main.line_jumps:
                    if not (lj in subroutine.line_jumps or lj == subroutine.line):
                        # a valid line jump that needs to be added to the correct node
                        subroutine.line_jumps.append(lj)
                
                self.remove(main)

            elif len(duplicates) == 3:
                cond_jump_node = [n for n in duplicates if n.prefix not in "MS"][0]
                if cond_jump_node.prefix != "D":
                    raise ValueError
                
                ms_nodes = [n for n in duplicates if n.prefix in "MS"]
                for node in ms_nodes:
                    for lj in node.line_jumps:
                        if not (lj in cond_jump_node.line_jumps or lj == cond_jump_node.line):
                            # a valid line jump that needs to be added to the correct node
                            cond_jump_node.line_jumps.insert(0, lj) # assumption is that a GOSUB statement is before a conditional jump, hence add it before the conditional jumps
                
                    self.remove(node)
            else:
                raise ValueError
        return None
    
