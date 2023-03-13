from xpotato.dataset.utils import default_pn_to_graph

from tuw_nlp.graph.utils import GraphFormulaPatternMatcher


PATTERNS = [
    # He is the brother of the composer... -> is_the_brother_of(He, composer)
    (
        "(u_0 / .* :nsubj (u_1 / .*) :nmod (u_2 / .* :case (u_3 / of)))",
        (0, 3),
        ((1,), (2,)),
    ),
    # The Greater Tokyo Area is the most populous metropolitan area... -> is(Area, area)
    (
        "(u_0 / .* :nsubj (u_1 / .*) :cop (u_2 / .*))",
        (2,),
        ((1,), (0,)),
    ),
    # The Greater Tokyo Area is the ... area in the world... -> is(A, a, in the world)
    (
        "(u_0 / .* :nsubj (u_1 / .*) :cop (u_2 / .*) :nmod (u_3 / .* :case (u_4 / .*)))",
        (2,),
        ((1,), (0,), (3, 4)),
    )
]


def get_mapping(graph):
    return {node["mapping"]: node for _, node in graph.nodes(data=True)}


def get_pred(head_ids, graph, all_heads):
    all_nodes = []
    for head_id in head_ids:
        nodes = [head_id]
        for i, j, data in graph.G.out_edges(head_id, data=True):
            if j in all_heads:
                continue
            # print(json.dumps(graph.to_json(), indent=4))
            if data["color"] in ("AMOD", "COP", "DET"):
                nodes.append(j)
        all_nodes += nodes

    return graph.subgraph(all_nodes)


def get_chunk_nodes(head_id, graph, all_heads):
    nodes = [head_id]
    for i, j, data in graph.G.out_edges(head_id, data=True):
        if j in all_heads:
            continue
        # print(json.dumps(graph.to_json(), indent=4))
        if data["color"] in ("NMOD", "AMOD", "ADVMOD", "DET", "COMPOUND", "APPOS", "FLAT", "CASE"):
            nodes += get_chunk_nodes(j, graph, all_heads)
    return nodes


def get_chunk(mapped_head_ids, graph, all_heads):
    all_nodes = []
    for mapped_head_id in mapped_head_ids:
        # print('toks:', graph.tokens, 'nodes:', graph.G.nodes(data=True), 'mapped head id:', mapped_head_id)
        nodes = get_chunk_nodes(mapped_head_id, graph, all_heads)
        all_nodes += nodes
    return graph.subgraph(all_nodes)


def graph_to_text(graph):
    return " ".join(tok for tok in graph.tokens if tok is not None)


def ud_to_triplets(graph):
    for patt, pred_ids, args in PATTERNS:
        # print('=====================')
        # print('patt, pred_ids, args:', patt, pred_ids, args)
        # print('=====================')
        patterns = [([patt], [], True)]
        matcher = GraphFormulaPatternMatcher(
            patterns, default_pn_to_graph, case_sensitive=False
        )
        for key, patt, subgraphs in matcher.match(graph.G, return_subgraphs=True):
            for subgraph in subgraphs:
                # print('subgraph:', subgraph.nodes(data=True))
                remaining_graph = graph.copy()
                mapping = {
                    data["mapping"]: node for node, data in subgraph.nodes(data=True)
                }
                arg_graphs = []
                arg_heads_by_arg = []
                all_heads = set()
                for arg_ids in args:
                    mapped_ids = [mapping[head_id] for head_id in arg_ids]
                    arg_heads_by_arg.append(mapped_ids)
                    all_heads |= set(mapped_ids)

                pred_heads = [mapping[pred_id] for pred_id in pred_ids]
                all_heads |= set(pred_heads)

                for head_ids in arg_heads_by_arg:
                    # print('remaining graph:', remaining_graph.str_nodes(), 'next arg head(s):', head_ids)
                    arg_graph = get_chunk(head_ids, remaining_graph, all_heads)
                    # print('arg graph:', arg_graph.tokens, arg_graph.str_nodes())
                    arg_graphs.append(arg_graph)
                    remaining_graph.remove_graph(arg_graph)

                pred_graph = get_pred(pred_heads, graph, all_heads)
                # print('pred graph:', pred_graph.tokens, pred_graph.str_nodes())
                # remaining_graph.remove_graph(pred_graph)

                yield graph_to_text(pred_graph), [
                    graph_to_text(arg_graph) for arg_graph in arg_graphs
                ]
