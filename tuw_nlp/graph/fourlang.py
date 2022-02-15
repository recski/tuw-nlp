import re
from collections import defaultdict

import networkx as nx
from networkx import algorithms
from networkx.algorithms.shortest_paths.generic import shortest_path_length
from tuw_nlp.graph.utils import Graph


class FourLang(Graph):
    def __init__(self, graph, root=None, lexical=None):
        super(FourLang, self).__init__()
        self.lexical = lexical
        self.G = graph

        self.root = root
        self.expanded = False

    def merge_definition_graph(self, graph, node, substitute=False):
        if graph.root != None:
            graph_root = graph.root
            F = nx.compose(self.G, graph.G)
            if substitute:
                F = nx.relabel_nodes(F, {node: graph_root})
                if node == self.root:
                    self.root = graph_root
                F.nodes[graph_root]['substituted'] = True
            else:
                F.add_edge(node, graph_root, color=0)
                F.nodes[node]['expanded'] = True
            self.G = F

    def append_zero_paths(self):
        edges = []
        for edge in self.G.edges(data=True):
            X = edge[0]
            Y = edge[1]
            color = edge[2]['color']

            zero_graph, nodes_to_append = self.find_zero_paths(Y)

            for node in nodes_to_append:
                if X != node:
                    edges.append((X, node, color))

            zero_graph, nodes_to_append = self.find_zero_paths(X)
            for node in nodes_to_append:
                node_edges = self.G.edges(node, data=True)
                for n in node_edges:
                    n_color = n[2]["color"]
                    if X != n[1]:
                        edges.append((X, n[1], n_color))

        edges = list(set(edges))
        for edge in edges:
            self.G.add_edge(edge[0], edge[1], color=edge[2])

    def find_zero_paths(self, from_node=None):
        if not from_node:
            from_node = self.root
        whitelist = []
        zero_graph = nx.DiGraph()
        zero_graph.add_node(from_node, name=self.G.nodes[from_node]["name"])
        delete_list = []
        for edge in self.G.edges(data=True):
            if not edge[2]["color"]:
                if edge[0] not in zero_graph.nodes():
                    zero_graph.add_node(
                        edge[0], name=self.G.nodes[edge[0]]["name"])
                if edge[1] not in zero_graph.nodes():
                    zero_graph.add_node(
                        edge[1], name=self.G.nodes[edge[1]]["name"])
                zero_graph.add_edge(edge[0], edge[1], color=0)

        for node in zero_graph.nodes(data=True):
            node_name = node[0]
            if algorithms.has_path(zero_graph, from_node, node_name):
                if node_name != from_node:
                    whitelist.append(node_name)
            else:
                delete_list.append(node_name)

        zero_graph.remove_nodes_from(delete_list)

        return zero_graph, whitelist

    def whitelisting(self, from_node=None):
        zero_graph, whitelist = self.find_zero_paths(from_node)

        self.G = zero_graph

    def merge(self, graph):
        F = nx.compose(self.G, graph.G)
        self.G = F

    def get_nodes(self):
        nodes_cleaned = []
        nodes = self.G.nodes(data=True)
        for node, data in nodes:
            cl = self.d_clean(node["name"])
            nodes_cleaned.append(cl)
        return nodes_cleaned
