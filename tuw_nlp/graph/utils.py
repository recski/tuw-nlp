from itertools import chain

import networkx as nx

from tuw_nlp.text.patterns.misc import (
    CHAR_REPLACEMENTS,
    PUNCT_REPLACEMENTS,
    MISC_REPLACEMENTS
)

dummy_isi_graph = '(dummy_0 / dummy_0)'
dummy_tree = 'dummy(dummy)'


def preprocess_edge_alto(edge):
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


def graph_to_isi_rec(graph, i):
    node = graph.nodes[i]
    lemma = preprocess_node_alto(preprocess_lemma(node['lemma']))
    pos = node['upos']
    isi = f"{pos}("
    for j, edge in graph[i].items():
        deprel = preprocess_edge_alto(edge['deprel'])
        isi += f"_{deprel}("
        isi += graph_to_isi_rec(graph, j)
        isi += f"), {pos}("

    isi += f"{lemma})" + ")"*len(graph[i])

    return isi


def get_root_id(graph):
    return list(graph[0].keys())[0]


def graph_to_isi(graph):
    root_id = get_root_id(graph)
    isi = graph_to_isi_rec(graph, root_id)
    return f"ROOT({isi})"
