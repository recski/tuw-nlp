import logging
import re
from copy import deepcopy
from itertools import chain, product

import networkx as nx
import penman as pn
from networkx.algorithms.isomorphism import DiGraphMatcher

from tuw_nlp import logger
from tuw_nlp.text.patterns.misc import (
    CHAR_REPLACEMENTS,
    MISC_REPLACEMENTS,
    PUNCT_REPLACEMENTS,
)
from tuw_nlp.text.utils import replace_emojis


dummy_isi_graph = "(dummy_0 / dummy_0)"
dummy_tree = "dummy(dummy)"


class GraphFormulaPatternMatcher:

    """
    Rule examples:
        1.) 3((u_800 / motion),(u_120 / swift))
        2.) path((u_120 / person),(u_800 / funny))
        3.) undirected((u_800 / terrible),(u_120 / friend))

        A rule like 1.) should be used, if the two subgraphs should be close to each other
        (generally in the same part of the sentence), but there might be some nodes along the way,
        like in the case of conjunctions.

        Rule 2.) is a more relaxed version of this, we want the second node to be connected to the first one.

        The rule 3.) is the least restrictive, but it could be useful if the graph in question would be disconnected,
        and we want the two subgraphs in the rule to be connected in some way.

        Note, that all of these rules require that the both of the subgraphs given is present in the main graph.

    Usage if we want to find the subgraphs that matched:
        gfpm = GraphFromulaPatternMatcher(pattern_list, pn_to_graph_converter, case_sensitive=False)
        feat_generator = gfpm.match(G, return_subgraphs=True)
        matches = []
        for key, feature, sub_graph in feat_generator:
            matches.append(sub_graph)
    """

    @staticmethod
    def node_matcher_case_insensitive(n1, n2):
        return GraphFormulaPatternMatcher.node_matcher(n1, n2, re.IGNORECASE)

    @staticmethod
    def node_matcher_case_sensitive(n1, n2):
        return GraphFormulaPatternMatcher.node_matcher(n1, n2, 0)

    @staticmethod
    def node_matcher(n1, n2, flags):
        logger.debug(f"matchig these: {n1}, {n2}")
        if n1["name"] is None or n2["name"] is None:
            return True

        return (
            True
            if (
                re.match(rf"\b({n2['name']})\b", n1["name"], flags)
                or n2["name"] == n1["name"]
            )
            else False
        )

    @staticmethod
    def edge_matcher_case_insensitive(n1, n2):
        return GraphFormulaPatternMatcher.edge_matcher(n1, n2, re.IGNORECASE)

    @staticmethod
    def edge_matcher_case_sensitive(n1, n2):
        return GraphFormulaPatternMatcher.edge_matcher(n1, n2, 0)

    @staticmethod
    def edge_matcher(e1, e2, flags):
        logger.debug(f"matchig these: {e1}, {e2}")
        return (
            True
            if re.match(rf"\b({str(e2['color'])})\b", str(e1["color"]), flags)
            else False
        )

    @staticmethod
    def get_matcher(graph, neg_graph, case_sensitive):
        if case_sensitive:
            return DiGraphMatcher(
                graph,
                neg_graph,
                node_match=GraphFormulaPatternMatcher.node_matcher_case_sensitive,
                edge_match=GraphFormulaPatternMatcher.edge_matcher_case_sensitive,
            )
        else:
            return DiGraphMatcher(
                graph,
                neg_graph,
                node_match=GraphFormulaPatternMatcher.node_matcher_case_insensitive,
                edge_match=GraphFormulaPatternMatcher.edge_matcher_case_insensitive,
            )

    def __init__(self, patterns, converter, case_sensitive=False):
        self.case_sensitive = case_sensitive
        self.reg_patterns = {
            re.compile(r"^(\d+)\((.*),(.*)\)"): self.max_distance,
            re.compile(r"^path\((.*),(.*)\)"): self.path_between,
            re.compile(r"^undirected\((.*),(.*)\)"): self.undirected,
        }
        self.patts = []

        for patts, negs, key in patterns:
            pos_patts = self.patt_list(patts, converter)
            neg_graphs = self.patt_list(negs, converter)
            self.patts.append((pos_patts, neg_graphs, key))

    def patt_list(self, patts, converter):
        patt_list = []
        for patt in patts:
            is_reg = False
            for p, func in self.reg_patterns.items():
                match = p.match(patt)
                if match is not None:
                    is_reg = True
                    groups = match.groups()
                    proc_groups = []
                    if len(groups) > 2:
                        proc_groups.append(int(groups[0]))
                        proc_groups.append(converter(groups[1])[0])
                        proc_groups.append(converter(groups[2])[0])
                    else:
                        proc_groups.append(converter(groups[0])[0])
                        proc_groups.append(converter(groups[1])[0])
                    patt_list.append((func, proc_groups))
                    break
            if not is_reg:
                patt_list.append(converter(patt)[0])
        return patt_list

    def max_distance(self, graph, node_data, subgraphs):
        max_dist, node1, node2 = node_data[0], node_data[1], node_data[2]
        node1_matches = []
        possible = self.digraph_matcher(graph, node1, node1_matches)
        if not possible:
            return False
        node2_matches = []
        possible = self.digraph_matcher(graph, node2, node2_matches)
        if not possible:
            return False
        for n1, n2 in product(node1_matches, node2_matches):
            n1_root = [n for n, d in n1.in_degree() if d == 0][0]
            n2_root = [n for n, d in n2.in_degree() if d == 0][0]
            try:
                if nx.shortest_path_length(graph, n1_root, n2_root) <= max_dist:
                    subgraphs.append(nx.compose(n1, n2))
                    return True
            except:
                continue
        return False

    def path_between(self, graph, nodes, subgraphs):
        node1_matches = []
        possible = self.digraph_matcher(graph, nodes[0], node1_matches)
        if not possible:
            return False
        node2_matches = []
        possible = self.digraph_matcher(graph, nodes[1], node2_matches)
        if not possible:
            return False
        for n1, n2 in product(node1_matches, node2_matches):
            n1_root = [n for n, d in n1.in_degree() if d == 0][0]
            n2_root = [n for n, d in n2.in_degree() if d == 0][0]
            try:
                if nx.has_path(graph, n1_root, n2_root):
                    subgraphs.append(nx.compose(n1, n2))
                    return True
            except:
                continue
        return False

    def undirected(self, graph, nodes, subgraphs):
        undirected_graph = graph.to_undirected().to_directed()
        return self.path_between(undirected_graph, nodes, subgraphs)

    def digraph_matcher(self, graph, pattern, subgraphs):
        matcher = GraphFormulaPatternMatcher.get_matcher(
            graph, pattern, self.case_sensitive
        )

        monomorphic_subgraphs = list(matcher.subgraph_monomorphisms_iter())
        if not len(monomorphic_subgraphs) == 0:
            for sub in monomorphic_subgraphs:
                mapping = sub
                subgraph = graph.subgraph(mapping.keys()).copy()
                # copying is essential, otherwise mapping gets overwritten if a node occurs in multiple matching subgraphs
                nx.set_node_attributes(subgraph, mapping, name="mapping")
                subgraphs.append(subgraph)
            return True
        return False

    def _neg_match(self, graph, negs):
        for neg_graph in negs:
            if isinstance(neg_graph, tuple):
                if neg_graph[0](graph, neg_graph[1]):
                    return True
            else:
                matcher = GraphFormulaPatternMatcher.get_matcher(
                    graph, neg_graph, case_sensitive=self.case_sensitive
                )
                if matcher.subgraph_is_monomorphic():
                    return True
        return False

    def match(self, graph, return_subgraphs=False):
        for i, (patt, negs, key) in enumerate(self.patts):
            logger.debug(f"matching this: {self.patts[i]}")
            neg_match = self._neg_match(graph, negs)

            if not neg_match:
                subgraphs = []
                pos_match = True
                for p in patt:
                    if isinstance(p, tuple):
                        if not p[0](graph, p[1], subgraphs):
                            pos_match = False
                            break
                    else:
                        if not self.digraph_matcher(graph, p, subgraphs):
                            pos_match = False
                            break

                if pos_match:
                    if return_subgraphs:
                        yield key, i, subgraphs
                    else:
                        yield key, i


def gen_subgraphs(M, no_edges):
    """M must be dict of dicts, see networkx.convert.to_dict_of_dicts.
    Generates dicts of dicts, use networkx.convert.from_dict_of_dicts"""
    if no_edges == 0:
        yield from ({v: {}} for v in M)
        return
    for s_graph in gen_subgraphs(M, no_edges - 1):
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


def pn_to_graph(raw_dl, edge_attr="color"):
    """Convert penman to networkx format
    raw_dl: raw string of penman format
    example: (k_4<root> / like :2 (k_6 / eat :2 (k_7 / sausage)) :1 (k_3 / dog :2-of (u_12 / HAS :1 (k_1 / Adam))))
    edges marked with k_* are mapped to UD nodes, u_* are unknown in UD
    """

    g = pn.decode(raw_dl)
    G = nx.DiGraph()
    node_to_id = {}
    root_id = None

    for i, trip in enumerate(g.instances()):
        node_id, name = trip[0], trip[2]

        node_to_id[node_id] = i

        if i == 0:
            root_id = i

        indicator = trip[0].split("_")[0]
        ud_id = trip[0].split("_")[1].split("<root>")[0]
        if ud_id.isnumeric():
            ud_id = int(ud_id)
        else:
            raise ValueError(f"{ud_id} is not a number")

        if indicator == "k":
            G.add_node(i, name=name, token_id=ud_id)
        elif indicator == "u":
            G.add_node(i, name=name, token_id=None)
        else:
            raise ValueError("Unknown indicator")

    for trip in g.edges():
        edge = trip[1].split(":")[1]
        if "-" in edge:
            assert edge.endswith("-of")
            edge = edge.split("-")[0]
            src = trip[2]
            tgt = trip[0]
        else:
            src = trip[0]
            tgt = trip[2]

        src_id = node_to_id[src]
        tgt_id = node_to_id[tgt]

        if edge != "UNKNOWN":
            G.add_edge(src_id, tgt_id)
            if edge.isnumeric():
                edge = int(edge)
            G[src_id][tgt_id].update({edge_attr: edge})

    return G, root_id


def bolinas_to_graph(bolinas_str, edge_attr="color"):
    """Convert bolinas to networkx format
    bolinas_str: raw string of bolinas format
    example: (n19. :obj (n21. :amod (n20. :ADJ n1020.) :NOUN n1021.) :VERB n1002.)
    """

    pn_str = re.sub(r" (n\d+\.\S*)\)", r" (\1))", bolinas_str)
    g = pn.decode(pn_str)
    G = nx.DiGraph()
    root_id = None

    for i, trip in enumerate(g.instances()):
        node_id = trip[0].split(".")[0]
        name = trip[0].split(".")[1].split("*")[0]

        if i == 0:
            root_id = node_id

        G.add_node(node_id, name=name)

    for trip in g.edges():
        edge = trip[1].split(":")[1]
        src = trip[0].split(".")[0]
        tgt = trip[2].split(".")[0]

        G.add_edge(src, tgt)
        G[src][tgt].update({edge_attr: edge})

    return G, root_id


def graph_to_bolinas(graph, name_attr="name", return_root=False, ext_node=None, keep_node_ids=True, add_names=False):
    nodes = {}
    pn_edges = []

    root_nodes, non_root_nodes = set(), set()
    for u, v, e in graph.edges(data=True):

        if v in root_nodes:
            root_nodes.remove(v)
        non_root_nodes.add(v)
        if u not in non_root_nodes:
            root_nodes.add(u)

        for node in u, v:
            if node not in nodes:
                label = ""
                if add_names and name_attr in graph.nodes[node]:
                    label = graph.nodes[node][name_attr]
                nodes[node] = f"n{node}.{label}" if node != ext_node else f"n{node}.{label}*"

        pn_edges.append((nodes[u], f':{e["color"]}', nodes[v]))

    assert len(root_nodes) == 1, f"graph has no unique root: {root_nodes}"
    top_node = root_nodes.pop()
    G = pn.Graph(pn_edges)
    bolinas_str = pn.encode(G, top=nodes[top_node], indent=0).replace("\n", " ")
    if not keep_node_ids:
        bolinas_str = re.sub(r'n[0-9]*\.', ".", bolinas_str)
    if return_root:
        return bolinas_str, top_node
    else:
        return bolinas_str


def graph_to_pn(graph, name_attr="name"):
    nodes = {}
    pn_edges, pn_nodes = [], []

    for u, v, e in graph.edges(data=True):
        for node in u, v:
            if node not in nodes:
                name = graph.nodes[node][name_attr]
                pn_id = f"u_{node}"
                nodes[node] = (pn_id, name)
                pn_nodes.append((pn_id, ":instance", name))

        pn_edges.append((nodes[u][0], f':{e["color"]}', nodes[v][0]))

    for node in graph.nodes():
        if node not in nodes:
            name = graph.nodes[node][name_attr]
            pn_id = f"u_{node}"
            nodes[node] = (pn_id, name)
            pn_nodes.append((pn_id, ":instance", name))

    G = pn.Graph(pn_nodes + pn_edges)

    try:
        # two spaces before edge name, because alto does it :)
        return pn.encode(G, indent=0).replace("\n", "  ")
    except pn.exceptions.LayoutError as e:
        words = [graph.nodes[node][name_attr] for node in graph.nodes()]
        logging.error(f"pn.encode failed on this graph: {words}")
        raise e


def postprocess_penman(graph_string):
    """The IRTG grammar returns labels with the corresponding UD ids.
    This function removes the UD ids from the labels and replaces penman ids with them.
    If UD id is not given, the penman ID remains.

    Example input:
    (u_1<root> / like_4  :2 (u_3 / eat_6  :2 (u_6 / sausage_7))  :1 (u_9 / dog_3  :2-of (u_12 / HAS  :1 (u_13 / Adam_1))))

    Example output:
    (k_4<root> / like :2 (k_6 / eat :2 (k_7 / sausage)) :1 (k_3 / dog :2-of (u_12 / HAS :1 (k_1 / Adam))))

    Args:
        graph_string (str): the input graph
    """

    g = pn.decode(graph_string)

    instances = {}
    relabel = {}

    for i in g.instances():
        if i[2] and "_" in i[2]:
            ud_id = i[2].split("_")[-1]
            label = "_".join(i[2].split("_")[:-1])
            if ud_id.isnumeric():
                new_id = f"k_{ud_id}"
                if g.top == i[0]:
                    new_id += "<root>"
                instances[new_id] = label
                relabel[i[0]] = new_id
            else:
                instances[i[0]] = i[2]
        else:
            instances[i[0]] = i[2]

    edges = []

    for edge in g.edges():
        src = relabel[edge[0]] if edge[0] in relabel else edge[0]
        tgt = relabel[edge[2]] if edge[2] in relabel else edge[2]

        edges.append((src, edge[1], tgt))

    nodes = [(k, ":instance", v) for k, v in instances.items()]

    return pn.encode(pn.Graph(nodes + edges), indent=0).replace("\n", "  ")


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


def check_if_str_is_penman(string):
    try:
        pn.decode(string)
        return True
    except Exception:
        return False


def preprocess_edge_alto(edge):
    if isinstance(edge, int):
        edge = str(edge)
    return edge.replace(":", "_").upper()


def preprocess_node_alto(edge):
    # import sys
    # sys.stderr.write(f'prepr_node_alto IN: {edge}\t')
    out = edge
    for a, b in chain(
        CHAR_REPLACEMENTS.items(), PUNCT_REPLACEMENTS.items(), MISC_REPLACEMENTS.items()
    ):
        out = out.replace(a, b)
    # sys.stderr.write(f'replace_emojis IN: {out}\t')
    out = replace_emojis(out)
    # sys.stderr.write(f'OUT: {out}\n')
    if out[0].isdigit():
        out = "X" + out
    return out


def preprocess_lemma(lemma):
    # sys.stderr.write(f'prepr_lemma IN: {lemma}\t')
    if lemma.startswith("|"):
        return lemma
    return lemma.split("|")[0]


def sen_to_graph(sen):
    """convert dependency-parsed stanza Sentence to nx.DiGraph"""
    G = nx.DiGraph()
    for word in sen.to_dict():
        if isinstance(word["id"], (list, tuple)):
            # token representing an mwe, e.g. "vom" ~ "von dem"
            continue
        G.add_node(word["id"], **word)
        G.add_edge(word["head"], word["id"], deprel=word["deprel"])
    return G


def get_node_attr(graph, i, convert_to_int, ud, preprocess):
    if ud:
        name = preprocess_lemma(graph.nodes[i]["lemma"])
    else:
        name, id_and_src = i.split("_")
        node_id = f"u_{id_and_src}"

    if preprocess:
        name = preprocess_node_alto(name)
    if ud:
        node_id = f"{name}_{i}"

    return node_id, name


def graph_to_isi_graph(
    graph, root_node, convert_to_int=False, ud=True, preprocess=True
):
    nodes = {}
    pn_edges, pn_nodes = [], []

    for u, v, e in graph.edges(data=True):
        for node in u, v:
            if node not in nodes:
                if ud:
                    if not graph.nodes[node]:
                        continue
                    name = preprocess_lemma(graph.nodes[node]["lemma"])
                    name = preprocess_node_alto(name)
                    id_and_src = f"{name}_{node}"
                else:
                    name, id_and_src = node.split("_")

                if node == root_node and not id_and_src.endswith("<root>"):
                    id_and_src += "<root>"
                if preprocess:
                    name = preprocess_node_alto(name)

                if ud:
                    pn_id = id_and_src
                else:
                    pn_id = f"u_{id_and_src}"

                nodes[node] = (pn_id, name)
                pn_nodes.append((pn_id, ":instance", name))

        if ud:
            if u in nodes and v in nodes:
                deprel = preprocess_edge_alto(e["deprel"])
                pn_edges.append((nodes[u][0], f":{deprel}", nodes[v][0]))
        else:
            pn_edges.append((nodes[u][0], f':{e["color"]}', nodes[v][0]))

    G = pn.Graph(pn_nodes + pn_edges)

    # two spaces before edge name, because alto does it :)
    return pn.encode(G, indent=0).replace("\n", "  ")


def graph_to_tree_rec(graph, i, convert_to_int=False, ud=True):
    node = graph.nodes[i]
    # sys.stderr.write(f'node: {node}\n')
    lemma = preprocess_node_alto(preprocess_lemma(node["lemma"]))
    pos = node["upos"]
    isi = f"{pos}("
    for j, edge in graph[i].items():
        deprel = preprocess_edge_alto(edge["deprel"])
        isi += f"_{deprel}("
        isi += graph_to_tree_rec(graph, j, convert_to_int)
        isi += f"), {pos}("

    lemma_int = f"{lemma}_{i}"
    isi += f"{lemma if not convert_to_int else lemma_int})" + ")" * len(graph[i])

    return isi


def get_root_id(graph, ud=True):
    if ud is True:
        return list(graph[0].keys())[0]
    else:
        roots = [n for n in graph.nodes if "root" in n]
        if len(roots) != 1:
            raise ValueError(f"no root in graph: {graph.nodes}")
        return roots[0]


def graph_to_isi(
    graph, convert_to_int=False, algebra="tree", ud=True, root_id=None, preprocess=True
):
    assert (
        ud is True or algebra == "graph"
    ), "converting non-UD graph to trees not supported"  # noqa
    if root_id is None:
        root_id = get_root_id(graph, ud)
    if algebra == "tree":
        isi = graph_to_tree_rec(graph, root_id, convert_to_int, ud)
    elif algebra == "graph":
        isi = graph_to_isi_graph(
            graph, root_id, convert_to_int=convert_to_int, ud=ud, preprocess=preprocess
        )
    return f"ROOT({isi})" if algebra == "tree" else isi


def read_and_write_graph(in_graph_str):
    G, root = read_alto_output(in_graph_str)
    return graph_to_isi(G, ud=False, algebra="graph", root_id=root, preprocess=False)


def test_graph_simple():
    in_graph_str = "(u_1<root> / begruenen  :2 (u_3 / Stand  :0 (u_6 / Wissenschaft  :0 (u_9 / technisch))  :0 (u_12 / entsprechend))  :2 (u_15 / Flachdaecher  :0 (u_18 / Dachneigung  :0 (u_21 / Grad  :0 (u_24 / fuenf)  :0 (u_27 / von))  :0 (u_30 / zu)  :0 (u_33 / bis))))"  # noqa
    out_graph_str = read_and_write_graph(in_graph_str)
    assert in_graph_str == out_graph_str


def test_graph_complex():
    in_graph_str = "(u_1<root> / ausbilden  :2 (u_11 / Dachflaeche  :0 (u_14 / Gebaeude))  :1-of (u_3 / als  :2 (u_4 / Flachdaecher  :0 (u_8 / begruent)))  :1-of (u_17 / auf  :2 (u_18 / Flaeche  :0 (u_22 / bezeichnet  :0 (u_25 / BB2)))))"  # noqa
    out_graph_str = read_and_write_graph(in_graph_str)
    assert in_graph_str == out_graph_str


if __name__ == "__main__":
    test_graph_simple()
    test_graph_complex()
    in_graph_str = "(u_1<root> / begruenen  :2 (u_3 / Stand  :0 (u_6 / Wissenschaft  :0 (u_9 / technisch))  :0 (u_12 / entsprechend))  :2 (u_15 / Flachdaecher  :0 (u_18 / Dachneigung  :0 (u_21 / Grad  :0 (u_24 / fuenf)  :0 (u_27 / von))  :0 (u_30 / zu)  :0 (u_33 / bis))))"  # noqa
    print(read_and_write_graph(in_graph_str))
