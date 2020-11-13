from tuw_nlp.grammar.lexicon import CFLLexicon, DefaultLexicon
from tuw_nlp.grammar.irtg import IRTGGrammar
from tuw_nlp.graph.utils import (
    get_root_id,
    graph_to_isi,
    preprocess_edge_alto,
    preprocess_lemma,
    preprocess_node_alto,
    sen_to_graph
)


class UD_Fourlang(IRTGGrammar):
    interpretations = {
        'ud': 'de.up.ling.irtg.algebra.graph.GraphAlgebra',
        'fourlang': 'de.up.ling.irtg.algebra.graph.GraphAlgebra'
    }
    lexicon = DefaultLexicon()

    def preprocess_input(self, input_sen):
        self.input_graph = sen_to_graph(input_sen)
        return graph_to_isi(self.input_graph, convert_to_int=True, algebra="graph")

    def gen_terminal_rules(self, lemma, pos, ind):
        fss = self.lexicon.get_terminal_rules(lemma, pos, ind)
        for i, fs in enumerate(fss):
            yield (
                f"{pos} -> {lemma}_{pos}_{ind}",
                {
                    'ud': fs[0],
                    'fourlang': fs[1]},
                'nonterminal')

    def gen_rules_rec(self, graph, i, parent=None):
        node = graph.nodes[i]
        lemma = preprocess_node_alto(preprocess_lemma(node['lemma']))
        pos = node['upos']
        yield from self.gen_terminal_rules(lemma, pos, i)
        for j, edge in graph[i].items():
            cnode = graph.nodes[j]
            clemma = preprocess_node_alto(graph.nodes[j]['lemma'])
            deprel = preprocess_edge_alto(edge['deprel'])
            cpos = cnode['upos']

            binary_fss = self.lexicon.get_dependency_rules(pos, deprel, cpos)
            for k, binary_fs in enumerate(binary_fss):
                yield (
                    f"{pos} -> {pos}_{deprel}_{cpos}_{k}({pos}, {cpos}) [0.1]",
                    {
                        'ud': f'{binary_fs[0]}',
                        'fourlang': f'{binary_fs[1]}'},
                    'nonterminal')

            if parent:
                subgraphs = self.lexicon.handle_subgraphs(lemma, pos, clemma, cpos, deprel, parent, i)

                if subgraphs:
                    yield from subgraphs


            yield from self.gen_rules_rec(graph, j, parent=(lemma, pos, deprel))

        for i, relation in enumerate(self.lexicon.relation_terms):
            terminal_fss = self.lexicon.get_relation_terminal(relation)

            yield (
                f"{relation} -> {relation}_{i}",
                {'ud': f"{terminal_fss[0]}",
                'fourlang': f"{terminal_fss[1]}"},
                "nonterminal"
            )

    def gen_rules(self):
        graph = self.input_graph
        root_id = get_root_id(graph)
        root_pos = graph.nodes[root_id]['upos']
        yield (
            f"S! -> ROOT({root_pos})", {
                "ud": "?1",
                "fourlang": "f_root(f_relation(?1))"},
            "start")

        yield from self.gen_rules_rec(graph, root_id)


class UD_FL(IRTGGrammar):
    interpretations = {
        'ud': 'de.up.ling.irtg.algebra.TreeWithAritiesAlgebra',
        'fl': 'de.up.ling.irtg.algebra.graph.GraphAlgebra'
    }
    lexicon = CFLLexicon()

    def preprocess_input(self, input_sen):
        self.input_graph = sen_to_graph(input_sen)
        return graph_to_isi(self.input_graph)

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
        node = graph.nodes[i]
        lemma = preprocess_node_alto(preprocess_lemma(node['lemma']))
        pos = node['upos']
        yield from self.gen_terminal_rules(lemma, pos)
        for j, edge in graph[i].items():
            cnode = graph.nodes[j]
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

    def gen_rules(self):
        graph = self.input_graph
        root_id = get_root_id(graph)
        root_pos = graph.nodes[root_id]['upos']
        yield (
            f"S! -> ROOT({root_pos})", {
                "ud": "ROOT_1(?1)",
                "fl": "?1"},
            "start")

        yield from self.gen_rules_rec(graph, root_id)
