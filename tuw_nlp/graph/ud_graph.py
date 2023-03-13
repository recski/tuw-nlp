import networkx as nx

from tuw_nlp.graph.graph import Graph
from tuw_nlp.graph.utils import preprocess_edge_alto


class UDGraph(Graph):
    def __init__(self, sen, text=None, tokens=None):

        graph = self.convert_to_networkx(sen)
        super(UDGraph, self).__init__(graph=graph, text=text, tokens=tokens, type="ud")
        self.ud_graph = sen

    def str_nodes(self):
        return " ".join(
            f"{i}_{data['name']}" for i, data in sorted(self.G.nodes(data=True))
        )

    def copy(self):
        new_graph = UDGraph(self.ud_graph, text=self.text, tokens=self.tokens)
        new_graph.G = self.G.copy()
        return new_graph

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

    def subgraph(self, nodes):
        # print("main graph:", self.str_nodes(), "nodes:", nodes)
        H = self.G.subgraph(nodes)
        tok_ids_to_keep = {data.get("token_id") for node, data in H.nodes(data=True)}
        new_tokens = [
            tok if i + 1 in tok_ids_to_keep else None for i, tok in enumerate(self.tokens)
        ]
        # print("main tokens:", self.tokens)
        # print("H.nodes:", H.nodes(data=True))
        # print("new tokens:", new_tokens)

        H.graph["tokens"] = new_tokens
        new_graph = UDGraph(self.ud_graph, text=None, tokens=new_tokens)
        # print("new graph tokens:", new_graph.tokens)
        new_graph.G = H
        # print(
        #    "new graph (subgraph):",
        #    new_graph.str_nodes(),
        #    "nodes:",
        #    new_graph.G.nodes(),
        # )
        return new_graph

    def convert_to_networkx(self, sen):
        """convert dependency-parsed stanza Sentence to nx.DiGraph"""
        G = nx.DiGraph()
        for word in sen.to_dict():
            if isinstance(word["id"], (list, tuple)):
                # token representing an mwe, e.g. "vom" ~ "von dem"
                continue
            G.add_node(word["id"], name=word["lemma"], token_id=word["id"])
            if word["deprel"] == "root":
                G.add_node(word["head"], name="root")
            G.add_edge(word["head"], word["id"])
            G[word["head"]][word["id"]].update(
                {"color": preprocess_edge_alto(word["deprel"])}
            )

        return G
