import networkx as nx

from tuw_nlp.graph.graph import Graph


class DRSGraph(Graph):
    def __init__(self, json_graph, text, tokens=None, type="drs"):
        graph = nx.cytoscape_graph(json_graph)

        self.counter = 0
        self.name_to_node = {}

        converted_graph = self.convert_to_networkx(graph)
        super().__init__(converted_graph, text, tokens, type)

    def convert_to_networkx(self, drs_graph):
        g = nx.DiGraph()

        for node, data in drs_graph.nodes(data=True):
            node_id = self.get_uid(node)
            node_name = data["value"]
            self._add_node(node_id, node_name, g)

        for source, target, data in drs_graph.edges(data=True):
            edge_color = data["label"]
            source_id = self.get_uid(source)
            target_id = self.get_uid(target)

            self._add_edge(source_id, target_id, edge_color, g)

        return g

    def _get_name_of_node(self, node):
        node = node.replace(".", "-")
        if node.startswith('"') and node.endswith('"'):
            return node[1:-1]
        elif "-" in node and node.split("-")[-1].isnumeric():
            return node.split("-")[0]
        else:
            return node

    def _add_node(self, node_id, node_label, graph):
        label = self._get_name_of_node(node_label)

        graph.add_node(node_id, name=label, orig_name=node_label, token_id=None)

    def _add_edge(self, source, target, color, graph):
        if color == "":
            color = "BOX"
        graph.add_edge(source, target, color=color)

    # Get a unique ID for naming nodes
    def get_uid(self, node_name):
        if node_name in self.name_to_node:
            return self.name_to_node[node_name]
        else:
            uid = "node_%d" % self.counter
            self.name_to_node[node_name] = uid
            self.counter += 1
            return uid
