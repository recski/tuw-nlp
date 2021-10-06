from tuw_nlp.grammar.lexicon import CFLLexicon, ENLexicon
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

    def __init__(self, **kwargs):
        self.lang = kwargs.get('lang') or "de"
        super(UD_FL, self).__init__(**kwargs)

        lexicon_map = {"en": ENLexicon(), "en_bio": ENLexicon(),  "de": CFLLexicon()}
        self.lexicon = lexicon_map[self.lang]

    def preprocess_input(self, input_sen):
        self.input_graph = sen_to_graph(input_sen)
        return graph_to_isi(self.input_graph)

    def gen_terminal_rules(self, lemma, pos, xpos):
        fss = self.lexicon.get_terminal_rules(lemma, pos, xpos)
        xpos_print = 'None' if xpos is None else preprocess_node_alto(xpos)
        for i, fs in enumerate(fss):
            yield (
                f"{pos} -> {lemma}_{pos}_{xpos_print}_{i}",
                {
                    'ud': f"{pos}_1({lemma}_0)",
                    'fl': fs},
                'nonterminal')

    def gen_rules_rec(self, graph, i, parent=None):
        node = graph.nodes[i]
        lemma = preprocess_node_alto(preprocess_lemma(node['lemma']))
        pos = node['upos']
        # xpos missing in a few rare cases, try 'US-Wirt.Minister:"Bürger, die'
        xpos = node.get('xpos')
        yield from self.gen_terminal_rules(lemma, pos, xpos)
        for j, edge in graph[i].items():
            cnode = graph.nodes[j]
            clemma = preprocess_node_alto(graph.nodes[j]['lemma'])
            deprel = preprocess_edge_alto(edge['deprel'])
            cpos = cnode['upos']

            binary_fss = self.lexicon.get_dependency_rules(pos, deprel, cpos)
            for k, binary_fs in enumerate(binary_fss):
                yield (
                    f"{pos} -> {pos}_{deprel}_{cpos}_{k}({deprel}_{cpos}, {pos}) [0.1]",  # noqa
                    {
                        'ud': f"{pos}_2(?1, ?2)",
                        'fl': f'{binary_fs}'},
                    'nonterminal')
            yield (
                f"{deprel}_{cpos} -> _{deprel}_{cpos}({cpos})",
                {
                    "ud": f"_{deprel}_1(?1)",
                    'fl': '?1'},
                'nonterminal')

            if parent:
                subgraphs = self.lexicon.handle_subgraphs(
                    lemma, pos, clemma, cpos, deprel, parent, i, j)

                if subgraphs:
                    yield from subgraphs

            yield from self.gen_rules_rec(
                graph, j, parent=(lemma, pos, deprel))

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
