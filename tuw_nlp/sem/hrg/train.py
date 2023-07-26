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


def get_pred_graph(ud_graph, pred, args):

    G_u = ud_graph.G.to_undirected()

    closest_nodes = {
        arg: min(
            nodes,
            key=lambda v: min(nx.shortest_path_length(G_u, v, u) for u in pred),
        )
        for arg, nodes in args.items()
    }

    print("closest nodes:", closest_nodes)
    pred_graph = ud_graph.subgraph(
        pred + list(closest_nodes.values()), handle_unconnected="shortest_path"
    )
    return pred_graph, closest_nodes


def get_pred_graph_bolinas(pred_graph, arg_anchors):
    nodes = {}
    pn_edges = []
    in_degrees, out_degrees = {}, {}
    arg_anchors_to_node = {}
    for arg, node in arg_anchors.items():
        arg_node = f"{arg}."
        arg_anchors_to_node[node] = arg_node
        pn_edges.append((arg_node, "A$", ""))
        in_degrees[arg_node] = 0
        out_degrees[arg_node] = 1

    print("arg anchors:", arg_anchors_to_node)
    for u, v, e in pred_graph.G.edges(data=True):
        print("u, v, e:", u, v, e)

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

        pn_edges.append((src, e["color"], tgt))

        in_degrees[tgt] += 1
        out_degrees[src] += 1

    print("pn_edges:", pn_edges)

    # find the unique root node so we can draw the graph
    root_nodes = set(
        node
        for node, count in in_degrees.items()
        if count == 0 and out_degrees[node] > 0
    )
    assert len(root_nodes) == 1, f"graph has no unique root: {root_nodes}"
    top_node = root_nodes.pop()

    G = pn.Graph(pn_edges)
    return pn.encode(G, top=top_node, indent=0).replace("\n", " ")


def main():
    nlp = stanza.Pipeline(
        lang="en",
        processors="tokenize,mwt,pos,lemma,depparse",
        tokenize_pretokenized=True,
    )
    vocab = Vocabulary(first_id=1000)
    for sen_idx, sen in enumerate(gen_tsv_sens(sys.stdin)):
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
        print(f"test{sen_idx} pred: {pred}, args: {args}")
        CoNLL.write_doc2conll(parsed_doc, f"out/test{sen_idx}.conll")
        print(f"wrote parse to test{sen_idx}.conll")

        agraphs_bolinas = []
        all_args_connected = True
        for arg, nodes in args.items():
            try:
                agraph_ud = ud_graph.subgraph(nodes)
            except UnconnectedGraphError:
                print(f"unconnected argument ({nodes}) in sentence {sen_idx}, skipping")
                all_args_connected = False
                continue

            agraph = agraph_ud.pos_edge_graph(vocab)
            agraphs_bolinas.append(agraph.to_bolinas())

        if not all_args_connected:
            print(f"sentence {sen_idx} had unconnected arguments, skipping")
            continue

        pred_graph_ud, arg_anchors = get_pred_graph(ud_graph, pred, args)
        pred_graph = pred_graph_ud.pos_edge_graph(vocab)

        with open(f"out/test{sen_idx}_pred.dot", "w") as f:
            f.write(pred_graph.to_dot())
        pred_graph_bolinas = get_pred_graph_bolinas(pred_graph, arg_anchors)

        with open(f"out/test{sen_idx}.hrg", "w") as f:
            f.write(f"S -> {pred_graph_bolinas}; 1.0 # 1\n")
            for i, agraph_bolinas in enumerate(agraphs_bolinas):
                f.write(f"A -> {agraph_bolinas}; 1.0 # {i+2}\n")
        print(f"wrote grammar to test{sen_idx}.hrg")

        idx_to_keep = [n for nodes in args.values() for n in nodes] + pred
        pruned_graph_bolinas = (
            ud_graph.subgraph(idx_to_keep, handle_unconnected="shortest_path")
            .pos_edge_graph(vocab)
            .to_bolinas()
        )
        with open(f"out/test{sen_idx}.graph", "w") as f:
            f.write(f"{pruned_graph_bolinas}\n")
        print(f"wrote graph to test{sen_idx}.graph")

        # print(graph.to_penman(name_attr='upos'))
    vocab_fn = "vocab.txt"
    vocab.to_file(f"{vocab_fn}")
    print(f"saved vocabulary to {vocab_fn}")


if __name__ == "__main__":
    main()
