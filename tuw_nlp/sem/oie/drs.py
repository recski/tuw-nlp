from xpotato.dataset.utils import default_pn_to_graph

from tuw_nlp.graph.utils import GraphFormulaMatcher

PATTERNS = [
    (
        "(u_0 / .* :Agent (u_1 / .*))",
        -1,
        (0, 1),
    ),
]


def drs_to_triplets(graph):
    print(graph.text)
    print(graph.tokens)
    print(graph.G.nodes(data=True))
    print(graph.to_penman())
    for patt, pred_id, args in PATTERNS:
        # print('=====================')
        # print('patt, pred_ids, args:', patt, pred_ids, args)
        # print('=====================')
        patterns = [([patt], [], True)]
        matcher = GraphFormulaMatcher(
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
                    arg_texts.append(graph.tokens[tok_id - 1])
                if pred_id == -1:
                    pred_text = "is"

                yield pred_text, tuple(arg_texts)
