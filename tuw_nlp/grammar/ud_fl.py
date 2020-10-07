from tuw_nlp.grammar.irtg import IRTGGrammar
from tuw_nlp.graph.utils import (
    get_root_id,
    graph_to_isi,
    preprocess_edge_alto,
    preprocess_lemma,
    preprocess_node_alto,
    sen_to_graph
)


class UD_FL(IRTGGrammar):
    interpretations = {
        'ud': 'de.up.ling.irtg.algebra.TreeWithAritiesAlgebra',
        'fl': 'de.up.ling.irtg.algebra.graph.GraphAlgebra'
    }

    def transform_input(self, input_sen):
        self.input_graph = sen_to_graph(input_sen)
        self.transformed_input = graph_to_isi(self.input_graph)

    def gen_terminal_rules(self, lemma, pos):
        fss = self.lexicon.get_terminal_rules(lemma, pos)
        for i, fs in enumerate(fss):
            yield (
                f"{pos} -> {lemma}_{pos}_{i}",
                {
                    'ud': f"{pos}_1({lemma}_0)",
                    'fl': fs},
                'nonterminal')

    def gen_rules_rec(self, graph, i):
        node = graph[i]
        lemma = preprocess_node_alto(preprocess_lemma(node['lemma']))
        pos = node['upos']
        yield from self.gen_terminal_rules(lemma, pos)
        for j, edge in graph[i].items():
            cnode = graph[j]
            deprel = preprocess_edge_alto(edge['deprel'])
            cpos = cnode['upos']

            binary_fss = self.lexicon.get_dependency_rules(pos, deprel, cpos)
            for k, binary_fs in enumerate(binary_fss):
                yield (
                    f"{pos} -> {pos}_{deprel}_{cpos}_{k}(_{deprel}, {pos})",
                    {
                        'ud': f"{pos}_2(?1, ?2)",
                        'fl': f'{binary_fs}'},
                    'nonterminal')
            yield (
                f"_{deprel} -> _{deprel}_{cpos}({cpos})",
                {
                    "ud": f"_{deprel}_1(?1)",
                    'fl': '?1'},
                'nonterminal')

            yield from self.gen_rules_rec(graph, j)

    def gen_rules(self, input_sen):
        graph = self.input_graph
        root_id = get_root_id(graph)
        root_pos = graph.nodes[root_id]['upos']
        yield (
            f"S! -> ROOT({root_pos})", {
                "ud": "ROOT_1(?1)",
                "fl": "?1"},
            "start")

        yield from self.get_rules_rec(graph, root_id)
