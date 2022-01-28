import logging
import re
from copy import deepcopy
from itertools import chain

import networkx as nx
import penman as pn
from networkx.algorithms.isomorphism import DiGraphMatcher
from tuw_nlp.text.patterns.misc import (CHAR_REPLACEMENTS, MISC_REPLACEMENTS,
                                        PUNCT_REPLACEMENTS)
from tuw_nlp.text.utils import replace_emojis

dummy_isi_graph = '(dummy_0 / dummy_0)'
dummy_tree = 'dummy(dummy)'


class GraphMatcher():
    @staticmethod
    def node_matcher(n1, n2):
        logging.debug(f'matchig these: {n1}, {n2}')
        if n1['name'] is None or n2['name'] is None:
            return True
        return n1['name'] == n2['name']

    @staticmethod
    def edge_matcher(e1, e2):
        logging.debug(f'matchig these: {e1}, {e2}')
        return e1['color'] == e2['color']

    def __init__(self, patterns):
        self.patts = [
            (pn_to_graph(patt)[0], key) for patt, key in patterns]

    def match(self, graph):
        for i, (patt, key) in enumerate(self.patts):
            logging.debug(f'matching this: {self.patts[i]}')
            matcher = DiGraphMatcher(
                graph, patt, node_match=GraphMatcher.node_matcher, edge_match=GraphMatcher.edge_matcher)
            if matcher.subgraph_is_monomorphic():
                logging.debug('MATCH!')
                yield key


class GraphFormulaMatcher():
    @staticmethod
    def node_matcher(n1, n2):
        logging.debug(f'matchig these: {n1}, {n2}')
        if n1['name'] is None or n2['name'] is None:
            return True

        return True if re.match(fr"\b({n2['name']})\b", n1['name'], re.IGNORECASE) else False

    @staticmethod
    def edge_matcher(e1, e2):
        logging.debug(f'matchig these: {e1}, {e2}')
        return True if re.match(fr"\b({str(e2['color'])})\b", str(e1['color']), re.IGNORECASE) else False

    def __init__(self, patterns, converter):
        self.patts = []

        for patts, negs, key in patterns:
            pos_patts = [converter(patt)[0] for patt in patts]
            neg_graphs = [converter(neg_patt)[0] for neg_patt in negs]
            self.patts.append((pos_patts, neg_graphs, key))

    def match(self, graph):
        for i, (patt, negs, key) in enumerate(self.patts):
            logging.debug(f'matching this: {self.patts[i]}')

            neg_match = False
            for neg in negs:
                matcher = DiGraphMatcher(
                    graph, neg, node_match=GraphFormulaMatcher.node_matcher, edge_match=GraphFormulaMatcher.edge_matcher)
                if matcher.subgraph_is_monomorphic():
                    neg_match = True
                    break

            pos_match = True
            for p in patt:
                matcher = DiGraphMatcher(
                    graph, p, node_match=GraphFormulaMatcher.node_matcher, edge_match=GraphFormulaMatcher.edge_matcher)
                if not matcher.subgraph_is_monomorphic():
                    pos_match = False
                    break

            if pos_match and not neg_match:
                yield key, i


def gen_subgraphs(M, no_edges):
    """M must be dict of dicts, see networkx.convert.to_dict_of_dicts.
    Generates dicts of dicts, use networkx.convert.from_dict_of_dicts"""
    if no_edges == 0:
        yield from ({v: {}} for v in M)
        return
    for s_graph in gen_subgraphs(M, no_edges-1):
        yield s_graph
        # print('==============================')
        # print('sgraph:', s_graph)
        # print('==============================')
        for node in M:
            for neighbor, edge in M[node].items():
                if node in s_graph and neighbor in s_graph[node]:
                    continue
                if node not in s_graph and neighbor not in s_graph:
                    continue

                # print('    node, neighbor, edge:', node, neighbor, edge)
                new_graph = deepcopy(s_graph)
                # print('    ngraph:', new_graph)
                if node not in new_graph:
                    new_graph[node] = {neighbor: edge}
                else:
                    new_graph[node][neighbor] = edge
                    new_graph[neighbor] = {}
                # print('    new_graph:', new_graph)
                yield new_graph


def pn_to_graph(raw_dl, edge_attr='color'):
    g = pn.decode(raw_dl)
    G = nx.DiGraph()

    for i, trip in enumerate(g.triples):
        if i == 0:
            root_id = int(trip[0].split("_")[1].split("<root>")[0])
            name = trip[2].split("<root>")[0]
            G.add_node(root_id, name=name)

        if trip[1] == ":instance":
            i, name = int(trip[0].split("<root>")[0].split("_")[1]), trip[2]
            G.add_node(i, name=name)

    for trip in g.triples:
        if trip[1] != ":instance":
            edge = trip[1].split(":")[1]
            if '-' in edge:
                assert edge.endswith('-of')
                edge = edge.split('-')[0]
                src = trip[2]
                tgt = trip[0]
            else:
                src = trip[0]
                tgt = trip[2]

            src_id = int(src.split("<root>")[0].split("_")[1])
            tgt_id = int(tgt.split("<root>")[0].split("_")[1])

            if edge != "UNKNOWN":
                G.add_edge(src_id, tgt_id)
                G[src_id][tgt_id].update({edge_attr: int(edge)})

    return G, root_id


def graph_to_pn(graph):
    nodes = {}
    pn_edges, pn_nodes = [], []

    for u, v, e in graph.edges(data=True):
        for node in u, v:
            if node not in nodes:
                name = graph.nodes[node]['name']
                pn_id = f'u_{node}'
                nodes[node] = (pn_id, name)
                pn_nodes.append((pn_id, ':instance', name))

        pn_edges.append((nodes[u][0], f':{e["color"]}', nodes[v][0]))

    for node in graph.nodes():
        if node not in nodes:
            name = graph.nodes[node]['name']
            pn_id = f'u_{node}'
            nodes[node] = (pn_id, name)
            pn_nodes.append((pn_id, ':instance', name))

    G = pn.Graph(pn_nodes + pn_edges)

    # two spaces before edge name, because alto does it :)
    return pn.encode(G, indent=0).replace('\n', '  ')


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
            id_to_word[trip[0].split("<root>")[0]] = trip[2]

    for trip in g.triples:
        if trip[1] != ":instance":
            head = trip[0].split("<root>")[0]
            dep = trip[2].split("<root>")[0]
            node1_unique = head.split("_")[1]
            node2_unique = dep.split("_")[1]
            dep1 = f"{id_to_word[head]}_{node1_unique}"
            dep2 = f"{id_to_word[dep]}_{node2_unique}"
            edge = trip[1].split(":")[1].split("-")[0]
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
    # import sys
    # sys.stderr.write(f'prepr_node_alto IN: {edge}\t')
    out = edge
    for a, b in chain(
            CHAR_REPLACEMENTS.items(), PUNCT_REPLACEMENTS.items(),
            MISC_REPLACEMENTS.items()):
        out = out.replace(a, b)
    # sys.stderr.write(f'replace_emojis IN: {out}\t')
    out = replace_emojis(out)
    # sys.stderr.write(f'OUT: {out}\n')
    if out[0].isdigit():
        out = "X" + out
    return out


def preprocess_lemma(lemma):
    # sys.stderr.write(f'prepr_lemma IN: {lemma}\t')
    if lemma.startswith('|'):
        return lemma
    return lemma.split('|')[0]


def sen_to_graph(sen):
    """convert dependency-parsed stanza Sentence to nx.DiGraph"""
    G = nx.DiGraph()
    for word in sen.to_dict():
        if isinstance(word['id'], (list, tuple)):
            # token representing an mwe, e.g. "vom" ~ "von dem"
            continue
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
        node_id = f'{name}_{i}'

    return node_id, name


def graph_to_isi_graph(
        graph, root_node, convert_to_int=False, ud=True, preprocess=True):
    nodes = {}
    pn_edges, pn_nodes = [], []

    for u, v, e in graph.edges(data=True):
        for node in u, v:
            if node not in nodes:
                if ud:
                    if not graph.nodes[node]:
                        continue
                    name = preprocess_lemma(graph.nodes[node]['lemma'])
                    name = preprocess_node_alto(name)
                    id_and_src = f'{name}_{node}'
                else:
                    name, id_and_src = node.split('_')

                if node == root_node and not id_and_src.endswith('<root>'):
                    id_and_src += '<root>'
                if preprocess:
                    name = preprocess_node_alto(name)

                if ud:
                    pn_id = id_and_src
                else:
                    pn_id = f'u_{id_and_src}'

                nodes[node] = (pn_id, name)
                pn_nodes.append((pn_id, ':instance', name))

        if ud:
            if u in nodes and v in nodes:
                deprel = preprocess_edge_alto(e["deprel"])
                pn_edges.append((nodes[u][0], f':{deprel}', nodes[v][0]))
        else:
            pn_edges.append((nodes[u][0], f':{e["color"]}', nodes[v][0]))

    G = pn.Graph(pn_nodes + pn_edges)

    # two spaces before edge name, because alto does it :)
    return pn.encode(G, indent=0).replace('\n', '  ')


def graph_to_tree_rec(graph, i, convert_to_int=False, ud=True):
    node = graph.nodes[i]
    # sys.stderr.write(f'node: {node}\n')
    lemma = preprocess_node_alto(preprocess_lemma(node['lemma']))
    pos = node['upos']
    isi = f"{pos}("
    for j, edge in graph[i].items():
        deprel = preprocess_edge_alto(edge['deprel'])
        isi += f"_{deprel}("
        isi += graph_to_tree_rec(graph, j, convert_to_int)
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
        isi = graph_to_tree_rec(graph, root_id, convert_to_int, ud)
    elif algebra == "graph":
        isi = graph_to_isi_graph(
            graph, root_id, convert_to_int=convert_to_int, ud=ud,
            preprocess=preprocess)
    return f"ROOT({isi})" if algebra == "tree" else isi


def read_and_write_graph(in_graph_str):
    G, root = read_alto_output(in_graph_str)
    return graph_to_isi(
        G, ud=False, algebra='graph', root_id=root, preprocess=False)


def test_graph_simple():
    in_graph_str = "(u_1<root> / begruenen  :2 (u_3 / Stand  :0 (u_6 / Wissenschaft  :0 (u_9 / technisch))  :0 (u_12 / entsprechend))  :2 (u_15 / Flachdaecher  :0 (u_18 / Dachneigung  :0 (u_21 / Grad  :0 (u_24 / fuenf)  :0 (u_27 / von))  :0 (u_30 / zu)  :0 (u_33 / bis))))"  # noqa
    out_graph_str = read_and_write_graph(in_graph_str)
    assert in_graph_str == out_graph_str


def test_graph_complex():
    in_graph_str = '(u_1<root> / ausbilden  :2 (u_11 / Dachflaeche  :0 (u_14 / Gebaeude))  :1-of (u_3 / als  :2 (u_4 / Flachdaecher  :0 (u_8 / begruent)))  :1-of (u_17 / auf  :2 (u_18 / Flaeche  :0 (u_22 / bezeichnet  :0 (u_25 / BB2)))))'  # noqa
    out_graph_str = read_and_write_graph(in_graph_str)
    assert in_graph_str == out_graph_str


if __name__ == '__main__':
    test_graph_simple()
    test_graph_complex()
    in_graph_str = "(u_1<root> / begruenen  :2 (u_3 / Stand  :0 (u_6 / Wissenschaft  :0 (u_9 / technisch))  :0 (u_12 / entsprechend))  :2 (u_15 / Flachdaecher  :0 (u_18 / Dachneigung  :0 (u_21 / Grad  :0 (u_24 / fuenf)  :0 (u_27 / von))  :0 (u_30 / zu)  :0 (u_33 / bis))))"  # noqa
    print(read_and_write_graph(in_graph_str))
