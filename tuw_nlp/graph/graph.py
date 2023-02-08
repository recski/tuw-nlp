import re

import networkx as nx
from networkx.readwrite import json_graph

from tuw_nlp.graph.utils import graph_to_pn, pn_to_graph


class Graph:
    def __init__(self, graph=None, text=None, tokens=None, type=None):
        if graph is None:
            self.G = nx.DiGraph()
        else:
            self.G = graph.copy()

        self.text = text
        self.type = type

        if tokens is None:
            self.tokens = []
        else:
            self.tokens = tokens

        self.G.graph["tokens"] = self.tokens
        self.G.graph["text"] = self.text
        self.G.graph["type"] = self.type

    def __dict__(self):
        return self.to_json()

    def to_json(self):
        s = json_graph.adjacency_data(self.G)
        return s

    def to_penman(self):
        return graph_to_pn(self.G)

    @staticmethod
    def from_networkx(G):
        tokens = G.graph["tokens"]
        text = G.graph["text"]
        type = G.graph["type"]

        return Graph(G, text, tokens, type)

    @staticmethod
    def from_penman(pn_graph):
        G, _ = pn_to_graph(pn_graph)

        return Graph(G)

    @staticmethod
    def from_json(json_str):
        G = nx.DiGraph()
        G = json_graph.adjacency_graph(json_str)
        tokens = G.graph["tokens"]
        text = G.graph["text"]
        type = G.graph["type"]

        return Graph(G, text, tokens, type)

    @staticmethod
    def d_clean(string):
        s = string
        for c in "\\=@-,'\".!:;<>/{}[]()#^?":
            s = s.replace(c, "_")
        s = (
            s.replace("$", "_dollars")
            .replace("%", "_percent")
            .replace("|", " ")
            .replace("*", " ")
        )
        if s == "#":
            s = "_number"
        keywords = ("graph", "node", "strict", "edge")
        if re.match("^[0-9]", s) or s in keywords:
            s = "X" + s
        return s

    def prune_graphs(self):
        """
        If the graph is not connected, prune it to the largest connected component
        """
        g = [
            c
            for c in sorted(
                nx.weakly_connected_components(self.G), key=len, reverse=True
            )
        ]
        if len(g) > 1:
            print(
                "WARNING: graph has multiple connected components, taking the largest"
            )
            g_pn = self.G.subgraph(g[0].copy())
        else:
            g_pn = self.G.copy()

        self.G = g_pn

    def to_dot(self, marked_nodes=set(), edge_color=None):
        show_graph = self.G.copy()
        show_graph.remove_nodes_from(list(nx.isolates(show_graph)))
        lines = ["digraph finite_state_machine {", "\tdpi=70;"]
        node_lines = []
        for node, n_data in show_graph.nodes(data=True):
            d_node = node
            if "name" in n_data:
                printname = self.d_clean(str(n_data["name"]))
            else:
                printname = d_node
            if (
                "expanded" in n_data
                and n_data["expanded"]
                and printname in marked_nodes
            ):
                node_line = '\t{0} [shape = circle, label = "{1}", \
                        style=filled, fillcolor=purple];'.format(
                    d_node, printname
                ).replace(
                    "-", "_"
                )
            elif "expanded" in n_data and n_data["expanded"]:
                node_line = '\t{0} [shape = circle, label = "{1}", \
                        style="filled"];'.format(
                    d_node, printname
                ).replace(
                    "-", "_"
                )
            elif "fourlang" in n_data and n_data["fourlang"]:
                node_line = '\t{0} [shape = circle, label = "{1}", \
                        style="filled", fillcolor=red];'.format(
                    d_node, printname
                ).replace(
                    "-", "_"
                )
            elif "substituted" in n_data and n_data["substituted"]:
                node_line = '\t{0} [shape = circle, label = "{1}", \
                        style="filled"];'.format(
                    d_node, printname
                ).replace(
                    "-", "_"
                )
            elif printname in marked_nodes:
                node_line = '\t{0} [shape = circle, label = "{1}", style=filled, fillcolor=lightblue];'.format(
                    d_node, printname
                ).replace(
                    "-", "_"
                )
            else:
                node_line = '\t{0} [shape = circle, label = "{1}"];'.format(
                    d_node, printname
                ).replace("-", "_")
            node_lines.append(node_line)
        lines += sorted(node_lines)

        edge_lines = []
        for u, v, edata in show_graph.edges(data=True):
            if "color" in edata:
                if edge_color is None:
                    edge_lines.append(
                        '\t{0} -> {1} [ label = "{2}" ];'.format(u, v, edata["color"])
                    )
                else:
                    edge_lines.append(
                        '\t{0} -> {1} [ label = "{2}", color = "{3}" ];'.format(
                            u, v, edata["color"], edge_color[edata["color"]]
                        )
                    )

        lines += sorted(edge_lines)
        lines.append("}")
        return "\n".join(lines)
