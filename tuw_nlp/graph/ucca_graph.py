import re
from xml.etree.ElementTree import fromstring

import networkx as nx
from ucca import layer0, layer1
from ucca.convert import from_standard

from tuw_nlp.graph.graph import Graph


class UCCAGraph(Graph):
    def __init__(self, passage, text, tokens, bilexical=True):
        self.passage = passage
        graph = self.convert_to_networkx(self.passage)
        self.remove_terminal_nodes(graph)

        bilexical_graph = self.get_bilexical_graph(graph)
        if bilexical:
            super().__init__(bilexical_graph, text, tokens, type="ucca")
        else:
            super().__init__(graph, text, tokens, type="ucca")

    def remove_terminal_nodes(self, graph):
        edges_to_remove = []
        edges_to_add = []

        for edge in graph.edges(data=True):
            if edge[2]["color"] == "Terminal":
                terminal = edge[1]

                parents = list(graph.predecessors(edge[0]))

                for p in parents:
                    edge_data = graph.get_edge_data(p, edge[0])
                    edges_to_add.append((p, terminal, edge_data))

                edges_to_remove.append(edge)

        for e in edges_to_add:
            graph.add_edge(e[0], e[1], **e[2])

        nodes_to_remove = []

        for e in edges_to_remove:
            graph.remove_edge(*e[:2])
            nodes_to_remove.append(e[0])

        nodes_to_remove = set(nodes_to_remove)
        for n in nodes_to_remove:
            graph.remove_node(n)

    def node_label(self, node):
        return re.sub("[^(]*\((.*)\)", "\\1", node.attrib.get("label", ""))

    def convert_to_networkx(self, passage):
        g = nx.DiGraph()

        for n in passage.layer(layer0.LAYER_ID).all:
            g.add_node(n.ID, name=n.text, token_id=n.para_pos - 1)

        for n in passage.layer(layer1.LAYER_ID).all:
            g.add_node(n.ID, name="NONTERMINAL", token_id=None)

        g.add_edges_from(
            [
                (
                    n.ID,
                    e.child.ID,
                    {
                        "color": "|".join(e.tags),
                        "style": "dashed" if e.attrib.get("remote") else "solid",
                    },
                )
                for layer in passage.layers
                for n in layer.all
                for e in n
            ]
        )

        return g

    def choose_best_successor(self, graph, nonterminal):
        priority = {
            "C": 0,
            "N": 1,
            "H": 2,
            "P": 3,
            "S": 4,
            "A": 5,
            "D": 6,
            "T": 7,
            "E": 8,
            "R": 9,
            "F": 10,
            "L": 11,
            "LR": 12,
            "LA": 13,
            "G": 14,
            "Terminal": 15,
            "U": 16,
        }

        successors = list(graph.successors(nonterminal))
        edge_to_scores = {}

        for successor in successors:
            edge_label = graph.get_edge_data(nonterminal, successor)["color"]

            edge_to_scores[successor] = priority[edge_label]

        priority_nodes = [
            key
            for key, value in edge_to_scores.items()
            if value == min(edge_to_scores.values())
        ]

        best_priority = None

        if len(priority_nodes) == 1:
            best_priority = priority_nodes[0]
        else:
            priority_numbers = []

            for i, priority in enumerate(priority_nodes):
                numbers = [int(num) for num in priority.split(".")]

                priority_numbers.append(numbers)

            min_idx = priority_numbers.index(min(priority_numbers))
            best_priority = priority_nodes[min_idx]

        return best_priority

    def search_head(self, graph, nonterminal):
        next_node = nonterminal

        best_successor = self.choose_best_successor(graph, next_node)

        while graph.nodes[best_successor]["token_id"] is None:
            next_node = best_successor

            best_successor = self.choose_best_successor(graph, next_node)

        return best_successor

    def get_bilexical_graph(self, graph):
        bilexical_graph = nx.DiGraph()
        bilexical_graph.add_nodes_from(
            [n for n in graph.nodes(data=True) if n[1]["token_id"] is not None]
        )

        nonterminal_nodes = [
            n for n in graph.nodes(data=True) if n[1]["token_id"] is None
        ]

        for nonterminal in nonterminal_nodes:
            head = self.search_head(graph, nonterminal[0])

            successors = list(graph.successors(nonterminal[0]))

            for successor in successors:
                if successor != head:
                    node = graph.nodes[successor]
                    terminal_successor = (
                        successor
                        if node["token_id"] is not None
                        else self.search_head(graph, successor)
                    )
                    parents = list(graph.predecessors(terminal_successor))
                    for p in parents:
                        if terminal_successor != head:
                            edge_data = graph.get_edge_data(p, terminal_successor)
                            bilexical_graph.add_edge(
                                head, terminal_successor, **edge_data
                            )

        return bilexical_graph

    def to_dot(self, graph=None, marked_nodes=set(), integ=True):
        if graph is None:
            graph = self.G

        lines = ["digraph finite_state_machine {", "\tdpi=70;"]
        # lines.append('\tordering=out;')
        # sorting everything to make the process deterministic
        node_lines = []
        node_to_name = {}
        for node, n_data in graph.nodes(data=True):
            if integ:
                d_node = self.d_clean(str(node))
            else:
                d_node = self.d_clean(n_data["name"]) if n_data["name"] else "None"
            printname = self.d_clean(n_data["name"]) if n_data["name"] else "None"
            # printname = d_node
            node_to_name[node] = printname
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
        for u, v, edata in graph.edges(data=True):
            if "color" in edata:
                d_node1 = self.d_clean(str(u))
                d_node2 = self.d_clean(str(v))
                edge_lines.append(
                    '\t{0} -> {1} [ label = "{2}" ];'.format(
                        d_node1, d_node2, edata["color"]
                    )
                )

        lines += sorted(edge_lines)
        lines.append("}")
        return "\n".join(lines)
