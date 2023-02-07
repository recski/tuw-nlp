import networkx as nx

from tuw_nlp.graph.graph import Graph
from tuw_nlp.graph.utils import preprocess_edge_alto


class UDGraph(Graph):
    def __init__(self, sen, text=None, tokens=None):

        graph = self.convert_to_networkx(sen)
        super(UDGraph, self).__init__(graph=graph, text=text, tokens=tokens, type="ud")
        self.ud_graph = sen

    def convert_to_networkx(self, sen):
        """convert dependency-parsed stanza Sentence to nx.DiGraph"""
        G = nx.DiGraph()
        root_id = None
        for word in sen.to_dict():
            if isinstance(word["id"], (list, tuple)):
                # token representing an mwe, e.g. "vom" ~ "von dem"
                continue
            G.add_node(word["id"], name=word["lemma"], token_id=word["id"])
            if word["deprel"] == "root":
                root_id = word["id"]
                G.add_node(word["head"], name="root")
            G.add_edge(word["head"], word["id"])
            G[word["head"]][word["id"]].update(
                {"color": preprocess_edge_alto(word["deprel"])}
            )

        return G
