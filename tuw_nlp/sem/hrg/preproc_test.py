import argparse
import sys

import stanza

import penman as pn

from tuw_nlp.common.vocabulary import Vocabulary
from tuw_nlp.graph.utils import graph_to_pn

from tuw_nlp.sem.hrg.common.utils import get_ud_graph, parse_doc, write_bolinas_graph, get_pred_and_args, \
    get_pred_arg_subgraph, create_sen_dir
from tuw_nlp.text.utils import gen_tsv_sens


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-f", "--first", type=int)
    parser.add_argument("-l", "--last", type=int)
    parser.add_argument("-o", "--out-dir", default="out", type=str)
    return parser.parse_args()


def write_pa_graph(out_dir, sen_idx, graph):
    with open(f"{out_dir}/sen{sen_idx}_pa_graph.dot", "w") as f:
        f.write(graph.to_dot())
    with open(f"{out_dir}/sen{sen_idx}_pa.graph", "w") as f:
        f.write(f"{graph_to_pn(graph.G)}\n")


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

        parsed_doc = parse_doc(nlp, sen, sen_idx, sen_dir, log)
        ud_graph = get_ud_graph(parsed_doc, sen_idx, sen_dir)
        write_bolinas_graph(sen_idx, ud_graph.pos_edge_graph(vocab), log, sen_dir)

        args, pred = get_pred_and_args(sen, sen_idx, log)
        pred_arg_subgraph = get_pred_arg_subgraph(ud_graph, pred, args, vocab, log)
        write_pa_graph(sen_dir, sen_idx, pred_arg_subgraph)
        # write_bolinas_graph(sen_idx, pred_arg_subgraph, log, sen_dir, name="_pa")


if __name__ == "__main__":
    args = get_args()
    main(args.first, args.last, args.out_dir)
