import argparse
import json
import sys

import stanza

from tuw_nlp.common.vocabulary import Vocabulary

from tuw_nlp.sem.hrg.common.utils import get_ud_graph, parse_doc, save_bolinas_str, get_pred_and_args, \
    get_pred_arg_subgraph, create_sen_dir, save_as_dot, add_oie_data_to_nodes
from tuw_nlp.text.utils import gen_tsv_sens


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-f", "--first", type=int)
    parser.add_argument("-l", "--last", type=int)
    parser.add_argument("-o", "--out-dir", default="out", type=str)
    return parser.parse_args()


def main(first=None, last=None, out_dir="out"):
    nlp = stanza.Pipeline(
        lang="en",
        processors="tokenize,mwt,pos,lemma,depparse",
        tokenize_pretokenized=True,
    )
    vocab = Vocabulary(first_id=1000)
    for sen_idx, sen in enumerate(gen_tsv_sens(sys.stdin)):
        if first is not None and sen_idx < first:
            continue
        if last is not None and last < sen_idx:
            break
        sen_dir = create_sen_dir(out_dir, sen_idx)
        print(f"processing sentence {sen_idx}, writing to {sen_dir}/sen{sen_idx}.log")
        log = open(f"{sen_dir}/sen{sen_idx}.log", "w")

        args, pred, node_to_label = get_pred_and_args(sen, sen_idx, log)

        parsed_doc = parse_doc(nlp, sen, sen_idx, sen_dir, log)

        ud_graph = get_ud_graph(parsed_doc, node_to_label)

        bolinas_graph = ud_graph.pos_edge_graph(vocab)
        save_as_dot(f"{sen_dir}/sen{sen_idx}_graph.dot", bolinas_graph, log)
        save_bolinas_str(f"{sen_dir}/sen{sen_idx}.graph", bolinas_graph, log)
        save_bolinas_str(f"{sen_dir}/sen{sen_idx}_labels.graph", bolinas_graph, log, add_names=True)

        pred_arg_subgraph = get_pred_arg_subgraph(ud_graph, pred, args, vocab, log)
        save_as_dot(f"{sen_dir}/sen{sen_idx}_pa_graph.dot", pred_arg_subgraph, log)
        save_bolinas_str(f"{sen_dir}/sen{sen_idx}_pa.graph", pred_arg_subgraph, log)
        with open(f"{sen_dir}/sen{sen_idx}_pa_nodes.json", "w") as f:
            json.dump([f"n{n}" for n in pred_arg_subgraph.G.nodes()], f)

        add_oie_data_to_nodes(ud_graph, node_to_label)
        save_as_dot(f"{sen_dir}/sen{sen_idx}_ud.dot", ud_graph, log)

        with open(f"{sen_dir}/sen{sen_idx}_node_to_label.json", "w") as f:
            json.dump(node_to_label, f)


if __name__ == "__main__":
    args = get_args()
    main(args.first, args.last, args.out_dir)
