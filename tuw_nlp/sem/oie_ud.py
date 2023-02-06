from xpotato.dataset.utils import default_pn_to_graph

from tuw_nlp.graph.utils import GraphFormulaMatcher


PATTERNS = [
    (
        "(u_0 / .* :nsubj (u_1 / .*) :nmod (u_2 / .* :case (u_3 / of)))",
        (0, 3),
        ((1,), (2,)),
    )
]


def get_mapping(graph):
    return {node["mapping"]: node for _, node in graph.nodes(data=True)}


def get_pred(head_ids, graph, mapping):
    all_nodes = []
    for head_id in head_ids:
        mapped_head_id = mapping[head_id]
        nodes = [mapped_head_id]
        for i, j, data in graph.G.out_edges(mapped_head_id, data=True):
            # print(json.dumps(graph.to_json(), indent=4))
            if data["color"] in ("AMOD", "COP", "DET"):
                nodes.append(j)
        all_nodes += nodes

    return graph.subgraph(all_nodes)


def get_chunk_nodes(head_id, graph):
    nodes = [head_id]
    for i, j, data in graph.G.out_edges(head_id, data=True):
        # print(json.dumps(graph.to_json(), indent=4))
        if data["color"] in ("AMOD", "DET", "COMPOUND", "APPOS", "FLAT"):
            nodes += get_chunk_nodes(j, graph)
    return nodes


def get_chunk(head_ids, graph, mapping):
    all_nodes = []
    for head_id in head_ids:
        mapped_head_id = mapping[head_id]
        nodes = get_chunk_nodes(mapped_head_id, graph)
        all_nodes += nodes
    return graph.subgraph(all_nodes)


def graph_to_text(graph):
    return " ".join(graph.tokens)


def ud_to_triplets(graph):
    for patt, pred_ids, args in PATTERNS:
        patterns = [([patt], [], True)]
        matcher = GraphFormulaMatcher(
            patterns, default_pn_to_graph, case_sensitive=False
        )
        for key, patt, subgraphs in matcher.match(graph.G, return_subgraphs=True):
            for subgraph in subgraphs:
                mapping = {
                    data["mapping"]: node for node, data in subgraph.nodes(data=True)
                }
                pred_graph = get_pred(pred_ids, graph, mapping)
                arg_graphs = [get_chunk(arg_ids, graph, mapping) for arg_ids in args]
                yield graph_to_text(pred_graph), [
                    graph_to_text(arg_graph) for arg_graph in arg_graphs
                ]
