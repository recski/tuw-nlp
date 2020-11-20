from itertools import chain

import networkx as nx
import penman as pn

from tuw_nlp.text.patterns.misc import (
    CHAR_REPLACEMENTS,
    PUNCT_REPLACEMENTS,
    MISC_REPLACEMENTS
)

dummy_isi_graph = '(dummy_0 / dummy_0)'
dummy_tree = 'dummy(dummy)'


def read_alto_output(raw_dl):
    id_to_word = {}

    g = pn.decode(raw_dl)

    G = nx.DiGraph()
    root = None

    for i, trip in enumerate(g.triples):
        if i == 0:
            ind = trip[0].split("_")[1].split("<root>")[0]
            name = trip[2].split("<root>")[0]
            root = f"{name}_{ind}"
        if trip[1] == ":instance":
            id_to_word[trip[0]] = trip[2]

    for trip in g.triples:
        if trip[1] != ":instance":
            node1_unique = trip[0].split("_")[1].split("<root>")[0]
            node2_unique = trip[2].split("_")[1].split("<root>")[0]
            dep1 = f"{id_to_word[trip[0]]}_{node1_unique}"
            dep2 = f"{id_to_word[trip[2]]}_{node2_unique}"
            edge = trip[1].split(":")[1]
            if edge != "UNKNOWN":
                G.add_edge(dep1, dep2, color=int(edge))

    if len(G.nodes()) == 0:
        G.add_node(root)

    return G, root


def preprocess_edge_alto(edge):
    if isinstance(edge, int):
        edge = str(edge)
    return edge.replace(':', '_').upper()


def preprocess_node_alto(edge):
    out = edge
    for a, b in chain(
            CHAR_REPLACEMENTS.items(), PUNCT_REPLACEMENTS.items(),
            MISC_REPLACEMENTS.items()):
        out = out.replace(a, b)
    if out[0].isdigit():
        out = "X" + out
    return out


def preprocess_lemma(lemma):
    return lemma.split('|')[0]


def sen_to_graph(sen):
    """convert dependency-parsed stanza Sentence to nx.DiGraph"""
    G = nx.DiGraph()
    for word in sen.to_dict():
        G.add_node(word['id'], **word)
        G.add_edge(word['head'], word['id'], deprel=word['deprel'])
    return G


def get_node_attr(graph, i, convert_to_int, ud, preprocess):
    if ud:
        name = preprocess_lemma(graph.nodes[i]['lemma'])
    else:
        name, id_and_src = i.split('_')
        node_id = f'u_{id_and_src}'

    if preprocess:
        name = preprocess_node_alto(name)
    if ud:
        node_id =  f'{name}_{i}'

    return node_id, name


def graph_to_isi_graph_rec(
        graph, i, convert_to_int=False, ud=True, preprocess=True):

    node_id, node_name = get_node_attr(
        graph, i, convert_to_int, ud, preprocess)
    isi = f"({node_id} / {node_name}"
    for j, edges in graph[i].items():
        edge_name = edges['deprel'] if ud else edges['color']
        edge_name = preprocess_edge_alto(edge_name)
        # two spaces before edge name, because alto does it :)
        isi += f'  :{edge_name} '
        isi += graph_to_isi_graph_rec(graph, j, convert_to_int, ud, preprocess)

    isi += ")"

    return isi


def graph_to_isi_tree_rec(graph, i, convert_to_int=False, ud=True):
    node = graph.nodes[i]
    lemma = preprocess_node_alto(preprocess_lemma(node['lemma']))
    pos = node['upos']
    isi = f"{pos}("
    for j, edge in graph[i].items():
        deprel = preprocess_edge_alto(edge['deprel'])
        isi += f"_{deprel}("
        isi += graph_to_isi_tree_rec(graph, j, convert_to_int)
        isi += f"), {pos}("

    lemma_int = f"{lemma}_{i}"
    isi += f"{lemma if not convert_to_int else lemma_int})" + ")"*len(graph[i])

    return isi


def get_root_id(graph, ud=True):
    if ud is True:
        return list(graph[0].keys())[0]
    else:
        roots = [n for n in graph.nodes if 'root' in n]
        if len(roots) != 1:
            raise ValueError(f'no root in graph: {graph.nodes}')
        return roots[0]


def graph_to_isi(
        graph, convert_to_int=False, algebra="tree", ud=True, root_id=None,
        preprocess=True):
    assert ud is True or algebra == 'graph', 'converting non-UD graph to trees not supported'  # noqa
    if root_id is None:
        root_id = get_root_id(graph, ud)
    if algebra == "tree":
        isi = graph_to_isi_tree_rec(graph, root_id, convert_to_int, ud)
    elif algebra == "graph":
        isi = graph_to_isi_graph_rec(
            graph, root_id, convert_to_int=convert_to_int, ud=ud,
            preprocess=preprocess)
    return f"ROOT({isi})" if algebra == "tree" else isi
