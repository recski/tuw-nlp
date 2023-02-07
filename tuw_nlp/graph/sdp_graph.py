import networkx as nx

from tuw_nlp.graph.graph import Graph


class SDPGraph(Graph):
    def __init__(self, graph=None, text=None, tokens=None, type=None, lemmas=None):

        networkx_graph = self.convert_to_networkx(graph)
        super().__init__(networkx_graph, text, tokens, type)

        self.lemmas = lemmas
        self.G.graph["lemmas"] = self.lemmas

    def convert_to_networkx(self, conllu_graph):
        g = nx.DiGraph()

        for token in conllu_graph:
            g.add_node(
                token["id"],
                name=token["form"],
                token_id=token["id"] - 1,
                lemma=token["lemma"],
                upos=token["upos"],
            )

        for token in conllu_graph:
            if token["deps"]:
                for dep in token["deps"]:
                    if len(dep) > 1 and dep[1] != 0:
                        g.add_edge(dep[1], token["id"], color=dep[0])

        return g
