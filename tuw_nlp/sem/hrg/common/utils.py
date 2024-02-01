import os.path
from collections import defaultdict

from stanza.utils.conll import CoNLL

from tuw_nlp.graph.graph import UnconnectedGraphError
from tuw_nlp.graph.ud_graph import UDGraph


def create_sen_dir(out_dir, sen_id):
    sen_dir = os.path.join(out_dir, str(sen_id))
    if not os.path.exists(sen_dir):
        os.makedirs(sen_dir)
    return sen_dir


def parse_doc(nlp, sen, sen_idx, out_dir, log):
    parsed_doc = nlp(" ".join(t[1] for t in sen))
    fn = f"{out_dir}/sen{sen_idx}_ud.dot"
    CoNLL.write_doc2conll(parsed_doc, fn)
    log.write(f"wrote parse to {fn}\n")
    return parsed_doc


def get_ud_graph(parsed_doc, node_to_label=None):
    parsed_sen = parsed_doc.sentences[0]
    return UDGraph(parsed_sen)


def get_pred_and_args(sen, sen_idx, log):
    args = defaultdict(list)
    pred = []
    node_to_label = defaultdict()
    for i, tok in enumerate(sen):
        label = tok[7].split("-")[0]
        if label == "O":
            continue
        elif label == "P":
            pred.append(i + 1)
            node_to_label[i + 1] = label
            continue
        args[label].append(i + 1)
        node_to_label[i + 1] = label
    log.write(f"sen{sen_idx} pred: {pred}, args: {args}, node_to_label: {node_to_label}\n")
    return args, pred, node_to_label


def save_bolinas_str(fn, graph, log):
    bolinas_graph = graph.to_bolinas()
    with open(fn, "w") as f:
        f.write(f"{bolinas_graph}\n")
    log.write(f"wrote graph to {fn}\n")


def save_as_dot(fn, graph, log):
    with open(fn, "w") as f:
        f.write(graph.to_dot())
    log.write(f"wrote graph to {fn}\n")


def get_pred_arg_subgraph(ud_graph, pred, args, vocab, log):
    idx_to_keep = [n for nodes in args.values() for n in nodes] + pred
    log.write(f"idx_to_keep: {idx_to_keep}\n")
    return ud_graph.subgraph(idx_to_keep, handle_unconnected="shortest_path").pos_edge_graph(vocab)


def check_args(args, log, sen_idx, ud_graph, vocab):
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
    return agraphs, all_args_connected


def add_oie_data_to_nodes(graph, node_to_label):
    if node_to_label:
        for n in graph.G.nodes:
            if n in node_to_label:
                graph.G.nodes[n]["name"] += f"\n{node_to_label[n]}"
