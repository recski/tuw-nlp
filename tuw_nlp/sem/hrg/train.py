import re
import sys
from collections import defaultdict

import networkx as nx
import penman as pn
import stanza
from stanza.utils.conll import CoNLL

from tuw_nlp.common.vocabulary import Vocabulary
from tuw_nlp.graph.graph import UnconnectedGraphError
from tuw_nlp.graph.ud_graph import UDGraph
from tuw_nlp.text.utils import gen_tsv_sens


def get_pred_graph(ud_graph, pred, args, log):

    G_u = ud_graph.G.to_undirected()

    closest_nodes = {
        arg: min(
            nodes,
            key=lambda v: min(nx.shortest_path_length(G_u, v, u) for u in pred),
        )
        for arg, nodes in args.items()
    }

    log.write(f"closest nodes: {closest_nodes}\n")
    pred_graph = ud_graph.subgraph(
        pred + list(closest_nodes.values()), handle_unconnected="shortest_path"
    )
    return pred_graph, closest_nodes


def get_pred_graph_bolinas(pred_graph, arg_anchors, args, log, keep_node_labels=True):
    nodes = {}
    pn_edges = []
    in_degrees, out_degrees = {}, {}
    arg_anchors_to_node = {}
    arg_anchors_to_arg_nodes = {}
    for arg, node in arg_anchors.items():
        arg_node = f"{arg}."
        arg_anchors_to_node[node] = arg_node
        in_degrees[arg_node] = 0
        out_degrees[arg_node] = 0
        arg_anchors_to_arg_nodes[node] = set(args[node])

    log.write(f"arg anchors: {arg_anchors_to_node}\n")
    log.write(f"arg_anchors_to_arg_nodes: {arg_anchors_to_arg_nodes}\n")

    anchor_nodes_handled = set()
    tail_anchors = set()

    for u, v, e in pred_graph.G.edges(data=True):
        log.write(f"{u} -{e['color']}-> {v}\n")

        # keep track of node labels and degrees
        for node in u, v:
            if node not in nodes:
                nodes[node] = f"n{node}."
                in_degrees[f"n{node}."] = 0
                out_degrees[f"n{node}."] = 0

        # discard leafs of args
        if u in arg_anchors_to_node and v >= 1000:
            continue

        src = arg_anchors_to_node.get(u, nodes[u])
        tgt = arg_anchors_to_node.get(v, nodes[v])

        if (
            v in arg_anchors_to_node
            and v not in anchor_nodes_handled
            and u not in arg_anchors_to_arg_nodes[v]
        ):
            pn_edges.append((tgt, "A$", ""))
            out_degrees[tgt] += 1
            anchor_nodes_handled.add(v)

            pn_edges.append((src, e["color"], tgt))
            in_degrees[tgt] += 1
            out_degrees[src] += 1

        elif (
            u in arg_anchors_to_node
            and u not in anchor_nodes_handled
            and v not in arg_anchors_to_arg_nodes[u]
        ):
            log.write(f"adding reverse arg edge based on this edge: {u}, {v}, {e}\n")
            pn_edges.append((src, "A$", nodes[u]))
            pn_edges.append((nodes[u], e["color"], tgt))
            out_degrees[src] += 1
            out_degrees[nodes[u]] += 1
            in_degrees[tgt] += 1
            in_degrees[nodes[u]] += 1
            anchor_nodes_handled.add(u)
            tail_anchors.add(u)

        else:
            pn_edges.append((src, e["color"], tgt))
            in_degrees[tgt] += 1
            out_degrees[src] += 1

    log.write(f"pn_edges: {pn_edges}\n")

    # find the unique root node so we can draw the graph
    root_nodes = set(
        node
        for node, count in in_degrees.items()
        if count == 0 and out_degrees[node] > 0
    )
    assert len(root_nodes) == 1, f"graph has no unique root: {root_nodes}"
    top_node = root_nodes.pop()

    G = pn.Graph(pn_edges)

    bolinas_str = pn.encode(G, top=top_node, indent=0).replace("\n", " ")

    if not keep_node_labels:
        bolinas_str = re.sub(r"n[0-9]*\.", ".", bolinas_str)
    return bolinas_str, tail_anchors


def get_next_edges(G, root_word, pred, arg_words, log):
    next_edges = defaultdict(list)
    for _, v, e in G.edges(root_word, data=True):
        if v in pred:
            next_edges['P'].append((e['color'], v))
        elif v in arg_words:
            next_edges['A'].append((e['color'], v))
        elif v >= 1000:
            root_pos = e['color']
        else:
            next_edges['X'].append((e['color'], v))
    log.write(f"next_edges: {next_edges}\n")
    return next_edges, root_pos


def gen_subseq_rules(G, pred_edges, arg_words, pred, log):
    for lhs, edges in pred_edges.items():
        for deprel, node in edges:
            next_edges, root_pos = get_next_edges(G, node, pred, arg_words, log)
            
            rule = f'{lhs} -> (. :{deprel} (.'
            for non_term in next_edges:
                rule += ' ' + ' '.join(f':{non_term}$' for _ in next_edges[non_term])
            rule += f' :{root_pos} .));\n'
            yield rule
            
            yield from gen_subseq_rules(G, next_edges, arg_words, pred, log)


def get_initial_rule(next_edges, root_pos):
    rule = 'S -> (.'
    for lhs in next_edges:
        rule += ' ' + ' '.join(f':{lhs}$' for _ in next_edges[lhs])
    rule += f' :{root_pos} .);\n'
    return rule


def create_rules_and_graph(sen_idx, ud_graph, pred, args, vocab, log):
    graph = get_pred_arg_subgraph(ud_graph, pred, args, vocab, log)
    write_graph(sen_idx, graph, log)
    root_word = next(nx.topological_sort(graph.G))
    log.write(f"root word: {root_word}\n")
    arg_words = set(w for nodes in args.values() for w in nodes)

    next_edges, root_pos = get_next_edges(graph.G, root_word, pred, arg_words, log)

    with open(f"out/test{sen_idx}.hrg", "w") as f:
        f.write(get_initial_rule(next_edges, root_pos))
        for rule in gen_subseq_rules(graph.G, next_edges, arg_words, pred, log):
            f.write(f'{rule}')
    log.write(f"wrote grammar to test{sen_idx}.hrg\n")


def create_rules_and_graph_old(sen_idx, ud_graph, pred, args, agraphs, vocab, log):

    pred_graph_ud, arg_anchors = get_pred_graph(ud_graph, pred, args, log)
    pred_graph = pred_graph_ud.pos_edge_graph(vocab)

    with open(f"out/test{sen_idx}_pred.dot", "w") as f:
        f.write(pred_graph.to_dot())
    pred_graph_bolinas, tail_anchors = get_pred_graph_bolinas(
        pred_graph, arg_anchors, args, log, keep_node_labels=False
    )
    log.write(f"tail_anchors: {tail_anchors}\n")
    
    if len(tail_anchors) != 0:
        print("tail_anchors:", tail_anchors)

    agraphs_bolinas = []
    for arg, agraph in agraphs.items():
        anchor = arg_anchors[arg]
        ext_node = anchor if anchor in tail_anchors else None
        agraphs_bolinas.append(
            agraph.to_bolinas(ext_node=ext_node, keep_node_labels=False)
        )

    with open(f"out/test{sen_idx}.hrg", "w") as f:
        f.write(f"S -> {pred_graph_bolinas};\n")
        for i, agraph_bolinas in enumerate(agraphs_bolinas):
            f.write(f"A -> {agraph_bolinas};\n")
    log.write(f"wrote grammar to test{sen_idx}.hrg\n")

    write_graph(sen_idx, get_pred_arg_subgraph(ud_graph, pred, args, vocab, log), log)


def write_graph(sen_idx, pred_arg_graph, log):
    pruned_graph_bolinas = pred_arg_graph.to_bolinas()
    with open(f"out/test{sen_idx}_graph.dot", "w") as f:
        f.write(pred_arg_graph.to_dot())
    with open(f"out/test{sen_idx}.graph", "w") as f:
        f.write(f"{pruned_graph_bolinas}\n")
    log.write(f"wrote graph to test{sen_idx}.graph\n")


def get_pred_arg_subgraph(ud_graph, pred, args, vocab, log):
    idx_to_keep = [n for nodes in args.values() for n in nodes] + pred
    log.write(f"idx_to_keep: {idx_to_keep}\n")
    return ud_graph.subgraph(idx_to_keep, handle_unconnected="shortest_path").pos_edge_graph(vocab)


def main():
    nlp = stanza.Pipeline(
        lang="en",
        processors="tokenize,mwt,pos,lemma,depparse",
        tokenize_pretokenized=True,
    )
    vocab = Vocabulary(first_id=1000)
    for sen_idx, sen in enumerate(gen_tsv_sens(sys.stdin)):
        print(f"processing sentence {sen_idx}, writing to out/test{sen_idx}.log")
        log = open(f"out/test{sen_idx}.log", "w")
        parsed_doc = nlp(" ".join(t[1] for t in sen))
        parsed_sen = parsed_doc.sentences[0]
        args = defaultdict(list)
        pred = []
        for i, tok in enumerate(sen):
            label = tok[7].split("-")[0]
            if label == "O":
                continue
            elif label == "P":
                pred.append(i + 1)
                continue
            args[label].append(i + 1)

        ud_graph = UDGraph(parsed_sen)
        # print(ud_graph.to_penman())
        with open(f"out/test{sen_idx}_ud.dot", "w") as f:
            f.write(ud_graph.to_dot())
        log.write(f"test{sen_idx} pred: {pred}, args: {args}\n")
        CoNLL.write_doc2conll(parsed_doc, f"out/test{sen_idx}.conll")
        log.write(f"wrote parse to test{sen_idx}.conll\n")

        agraphs = {}
        all_args_connected = True
        for arg, nodes in args.items():
            try:
                agraph_ud = ud_graph.subgraph(nodes)
            except UnconnectedGraphError:
                log.write(
                    f"unconnected argument ({nodes}) in sentence {sen_idx}, skipping\n"
                )
                all_args_connected = False
                continue

            agraphs[arg] = agraph_ud.pos_edge_graph(vocab)

        if not all_args_connected:
            log.write(f"sentence {sen_idx} had unconnected arguments, skipping\n")
            continue

        # create_rules_and_graph_old(sen_idx, ud_graph, pred, args, agraphs, vocab, log)
        create_rules_and_graph(sen_idx, ud_graph, pred, args, vocab, log)

    vocab_fn = "vocab.txt"
    vocab.to_file(f"{vocab_fn}")
    print(f"saved vocabulary to {vocab_fn}")


if __name__ == "__main__":
    main()
