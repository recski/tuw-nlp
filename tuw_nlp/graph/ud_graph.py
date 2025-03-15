from anyascii import anyascii
import networkx as nx
from networkx.readwrite import json_graph
from stanza.models.common.doc import Sentence

from tuw_nlp.graph.graph import Graph, UnconnectedGraphError
from tuw_nlp.graph.utils import preprocess_edge_alto


class UDGraph(Graph):
    @staticmethod
    def from_json(data):
        sen = Sentence(data["stanza_sen"])
        sen.text = data["stanza_text"]
        text, tokens = data["text"], data["tokens"]
        G = json_graph.adjacency_graph(data["graph"])
        assert G.graph["type"] == "ud"
        assert G.graph["text"] == text
        assert (
            G.graph["tokens"] == tokens
        ), f'tokens mismatch:\n{G.graph["tokens"]=}\n{tokens=}'
        ud_graph = UDGraph(sen, text, tokens, G)
        return ud_graph

    def __init__(self, sen, text=None, tokens=None, graph=None):
        """Initialize UDGraph instance.
        First argument must be a stanza sentence and by default it is used to infer the graph"""

        if graph is None:
            graph = self.convert_to_networkx(sen)
        super(UDGraph, self).__init__(graph=graph, text=text, tokens=tokens, type="ud")
        self.stanza_sen = sen

    def to_json(self):
        data = {
            "graph": json_graph.adjacency_data(self.G),
            "text": self.text,
            "tokens": self.tokens,
            "stanza_sen": self.stanza_sen.to_dict(),
            "stanza_text": self.stanza_sen.text,
        }
        return data

    def __str__(self):
        return f"UDGraph({self.str_nodes()})"

    def __repr__(self):
        return self.__str__()

    def str_node(self, node, data):
        node_str = f"{node}_{data['name']}"
        if data.get("inferred") is True:
            node_str += "*"
        return node_str

    def str_nodes(self):
        return " ".join(
            f"{self.str_node(node, self.G.nodes[node])}" for node in self.lextop
        )

    def copy(self):
        new_graph = UDGraph(self.stanza_sen, text=self.text, tokens=self.tokens)
        new_graph.G = self.G.copy()
        return new_graph

    @property
    def root(self):
        return next(nx.topological_sort(self.G))

    def remove_graph(self, other):
        g_to_remove = other.G.copy()
        tok_ids_to_remove = {
            data.get("token_id") for node, data in g_to_remove.nodes(data=True)
        }
        self.tokens = [
            tok if i + 1 not in tok_ids_to_remove else None
            for i, tok in enumerate(self.tokens)
        ]
        self.text = None
        self.G.remove_nodes_from(g_to_remove)

    def _subgraph_infer_new_nodes(self, nodes, handle_unconnected):
        H = self.G.subgraph(nodes)

        # case 1: induced subgraph is connected, nothing to do
        if nx.is_weakly_connected(H):
            return set(nodes), set()

        # case 2: induced subgraph was expected to be connected, raise error
        if handle_unconnected is None:
            print(self.to_dot())
            print(Graph.nx_graph_to_dot(H))
            raise UnconnectedGraphError(
                f"subgraph induced by nodes {nodes} in {self} is not connected and handle_unconnected is not specified"
            )

        # case 3: induce connected subgraph using shortest paths between components
        if handle_unconnected == "shortest_path":
            inferred_nodes = set()
            new_nodes = set(nodes)  # a copy of the original nodes parameter to expand
            components = [
                list(node_set) for node_set in nx.weakly_connected_components(H)
            ]
            src = components[0][0]  # a dedicated node in a dedicated component
            G_u = (
                self.G.to_undirected()
            )  # an undirected version of G to search for shortest paths
            for comp in components[1:]:
                path = nx.shortest_path(G_u, src, comp[0])
                # print(f'shortest path between {src} and {comp[0]}: {path}')
                for node in path:
                    if node not in new_nodes:
                        new_nodes.add(node)
                        inferred_nodes.add(node)

            return new_nodes, inferred_nodes

        else:
            raise ValueError(
                f"unknown value of handle_unconnected: {handle_unconnected}"
            )

    @property
    def inferred_nodes(self):
        return [node for node, data in self.G.nodes(data=True) if data.get("inferred")]

    def index_inferred_nodes(self):
        return self.index_nodes(self.inferred_nodes)

    def subgraph(self, nodes, handle_unconnected=None):
        new_nodes, inferred_nodes = self._subgraph_infer_new_nodes(
            nodes, handle_unconnected
        )

        # snippet from networkx docs on networkx.Graph.subgraph
        H = nx.DiGraph()
        H.add_nodes_from((n, self.G.nodes[n]) for n in new_nodes)
        H.add_edges_from(
            (n, nbr, d)
            for n, nbrs in self.G.adj.items()
            if n in new_nodes
            for nbr, d in nbrs.items()
            if nbr in new_nodes
        )

        for node in inferred_nodes:
            H.nodes()[node]["inferred"] = True

        tok_ids_to_keep = {data.get("token_id") for node, data in H.nodes(data=True)}
        new_tokens = [
            tok if i + 1 in tok_ids_to_keep else None
            for i, tok in enumerate(self.tokens)
        ]
        H.graph["tokens"] = new_tokens

        new_graph = UDGraph(self.stanza_sen, text=None, tokens=new_tokens, graph=H)
        return new_graph

    def pos_edge_graph(self):
        H = self.G.copy()
        for u, v, d in H.edges(data=True):
            d["color"] = d["color"].lower()
        for node, data in self.G.nodes(data=True):
            word = data["name"]
            leaf_node_id = 1000
            if "token_id" in data:
                leaf_node_id += data["token_id"]
            H.add_node(leaf_node_id, name=word)
            H.add_edge(node, leaf_node_id, color=data["upos"])
            nx.set_node_attributes(H, {node: {"name": ""}})
        return Graph.from_networkx(H)

    def convert_to_networkx(self, sen):
        """convert dependency-parsed stanza Sentence to nx.DiGraph"""
        G = nx.DiGraph()
        self.tok_ids_to_nodes = {}
        for i, word in enumerate(sen.to_dict()):
            if isinstance(word["id"], (list, tuple)):
                # token representing an mwe, e.g. "vom" ~ "von dem"
                continue
            name = word.get("lemma", word["text"])
            node_id = i+1
            G.add_node(
                node_id,
                name=name,
                token_id=word["id"],
                upos=word["upos"],
                asciiname=anyascii(name),
            )
            self.tok_ids_to_nodes[word["id"]] = node_id
            if word["deprel"] == "root":
                G.add_node(0, name="root", upos="ROOT")
                self.tok_ids_to_nodes[0] = 0

        for i, word in enumerate(sen.to_dict()):
            if not isinstance(word["id"], int):
                # multi-word token
                continue
            head_node = self.tok_ids_to_nodes[word["head"]]
            node_id = i + 1
            G.add_edge(head_node, node_id)
            G[head_node][node_id].update({"color": preprocess_edge_alto(word["deprel"])})

        return G
