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
    CoNLL.write_doc2conll(parsed_doc, f"{out_dir}/sen{sen_idx}.conll")
    log.write(f"wrote parse to test{sen_idx}.conll\n")
    return parsed_doc


def get_ud_graph(parsed_doc, sen_idx, out_dir):
    parsed_sen = parsed_doc.sentences[0]
    ud_graph = UDGraph(parsed_sen)
    with open(f"{out_dir}/sen{sen_idx}_ud.dot", "w") as f:
        f.write(ud_graph.to_dot())
    return ud_graph


def get_pred_and_args(sen, sen_idx, log):
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
    log.write(f"sen{sen_idx} pred: {pred}, args: {args}\n")
    return args, pred


def write_bolinas_graph(sen_idx, graph, log, out_dir, name=""):
    pruned_graph_bolinas = graph.to_bolinas()
    with open(f"{out_dir}/sen{sen_idx}{name}_graph.dot", "w") as f:
        f.write(graph.to_dot())
    with open(f"{out_dir}/sen{sen_idx}{name}.graph", "w") as f:
        f.write(f"{pruned_graph_bolinas}\n")
    log.write(f"wrote graph to test{sen_idx}{name}.graph\n")


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


def add_oie_data_to_parsed_doc(sen, parsed_doc):
    assert len(sen) == len(parsed_doc.sentences[0].tokens)
    for i, token in enumerate(parsed_doc.sentences[0].tokens):
        label = sen[i][7].split("-")[0]
        if label.startswith("A") or label.startswith("P"):
            token.words[0].lemma += f"\n{label}"
