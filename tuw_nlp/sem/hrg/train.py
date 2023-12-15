import argparse
import sys

import stanza

from tuw_nlp.common.vocabulary import Vocabulary
from tuw_nlp.sem.hrg.common.utils import parse_doc, get_ud_graph, get_pred_and_args, check_args
from tuw_nlp.text.utils import gen_tsv_sens


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-f", "--first", type=int)
    parser.add_argument("-l", "--last", type=int)
    parser.add_argument("-m", "--method", default="per_word", type=str)
    parser.add_argument("-o", "--out-dir", default="out", type=str)
    return parser.parse_args()


def main(first=None, last=None, method="per_word", out_dir="out"):
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
        print(f"processing sentence {sen_idx}, writing to {out_dir}/sen{sen_idx}.log")
        log = open(f"{out_dir}/sen{sen_idx}.log", "w")

        parsed_doc = parse_doc(nlp, sen, sen_idx, out_dir, log)
        ud_graph = get_ud_graph(parsed_doc, sen_idx, out_dir)
        args, pred = get_pred_and_args(sen, sen_idx, log)
        arg_graphs, all_args_connected = check_args(args, log, sen_idx, ud_graph, vocab)

        if not all_args_connected:
            log.write(f"sentence {sen_idx} had unconnected arguments, skipping\n")
            continue

        if method == "per_word":
            from tuw_nlp.sem.hrg.generation.per_word import create_rules_and_graph
            create_rules_and_graph(sen_idx, ud_graph, pred, args, vocab, log, out_dir)
        elif method == "per_arg":
            from tuw_nlp.sem.hrg.generation.per_arg import create_rules_and_graph
            create_rules_and_graph(sen_idx, ud_graph, pred, args, arg_graphs, vocab, log, out_dir)

    vocab_fn = "vocab.txt"
    vocab.to_file(f"{vocab_fn}")
    print(f"saved vocabulary to {vocab_fn}")


if __name__ == "__main__":
    args = get_args()
    main(args.first, args.last, args.method, args.out_dir)
