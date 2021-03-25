import networkx as nx
from networkx.convert import from_dict_of_dicts as fdd
from networkx.convert import to_dict_of_dicts as tdd

from tuw_nlp.common.vocabulary import Vocabulary
from tuw_nlp.graph.utils import gen_subgraphs


class LexGraphs():
    def __init__(self):
        self.vocab = Vocabulary()

    def from_plain(self, G):
        return nx.relabel_nodes(
            G, lambda n: self.vocab.get_id(G.nodes[n]['name']))

    def add_names(self, G):
        for node in G.nodes:
            G.nodes[node]['name'] = self.vocab.get_word(node)

    def from_tuple(self, T):
        G = fdd(
            {v1: {v2: {"color": e} for v2, e in edges} for v1, edges in T})
        self.add_names(G)
        return G

    def _dict_to_tuple(self, D):
        return tuple(sorted(
            (node, tuple(sorted(
                (n, e['color']) for n, e in edges.items())))
            for node, edges in D.items()))

    def gen_lex_subgraphs(self, G, n):
        H = self.from_plain(G)
        H_dict = tdd(H)
        for sgraph_dict in gen_subgraphs(H_dict, n):
            sgraph = fdd(sgraph_dict, create_using=nx.MultiDiGraph())
            for node in sgraph.nodes:
                sgraph.nodes[node]['name'] = self.vocab.get_word(node)

            sgraph_tuple = self._dict_to_tuple(sgraph_dict)

            yield sgraph_tuple, sgraph
