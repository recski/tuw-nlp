import networkx as nx
import re


class Graph:
    def __init__(self):
        self.G = nx.DiGraph()

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
