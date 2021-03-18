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

    def gen_lex_subgraphs(self, G, n):
        H = self.from_plain(G)
        H_dict = tdd(H)
        for sgraph_dict in gen_subgraphs(H_dict, n):
            sgraph = fdd(sgraph_dict)
            for node in sgraph.nodes:
                sgraph.nodes[node]['name'] = self.vocab.get_word(node)

            sgraph_tuple = tuple(sorted(
                (node, tuple(sorted(
                    (n, e['color']) for n, e in edges.items())))
                for node, edges in sgraph_dict.items()))

            yield sgraph_tuple, sgraph
