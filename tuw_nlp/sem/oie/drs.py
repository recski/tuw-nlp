from xpotato.dataset.utils import default_pn_to_graph

from tuw_nlp.graph.utils import GraphFormulaPatternMatcher

PATTERNS = [
    (
        "(u_0 / .* :Agent (u_1 / .*) :User|Theme (u_2 / .*))",
        0,
        (1, 2),
    ),
    #(
    #    "(u_0 / .* :Agent (u_1 / .*))",
    #    -1,
    #    (0, 1),
    #),
]


def drs_to_triplets(graph):
    for patt, pred_id, args in PATTERNS:
        # print('=====================')
        # print('patt, pred_ids, args:', patt, pred_ids, args)
        # print('=====================')
        patterns = [([patt], [], True)]
        matcher = GraphFormulaPatternMatcher(
            patterns, default_pn_to_graph, case_sensitive=False
        )
        for key, patt, subgraphs in matcher.match(graph.G, return_subgraphs=True):
            for subgraph in subgraphs:
                mapping = {
                    data["mapping"]: data['token_id'] for node, data in subgraph.nodes(data=True)
                }
                arg_texts = []
                for arg_id in args:
                    tok_id = mapping[arg_id]
                    if tok_id is not None:
                        arg_texts.append(graph.tokens[tok_id - 1])

                if len(arg_texts) == 0:
                    continue

                if pred_id == -1:
                    pred_text = "is"
                else:
                    pred_tok_id = mapping[pred_id]
                    if pred_tok_id is None:
                        continue
                    pred_text = graph.tokens[pred_tok_id - 1]

                yield pred_text, tuple(arg_texts)
