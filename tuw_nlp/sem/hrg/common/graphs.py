import itertools

import networkx as nx


def get_all_subgraphs(G, n):
    subgraphs = []
    for subgraph_nodes in itertools.combinations(G.nodes, n):
        H = G.subgraph(subgraph_nodes)
        if nx.is_weakly_connected(H):
            subgraphs.append(H)
    return subgraphs


def edge_matcher(e1, e2):
    return e1['color'] == e2["color"]
