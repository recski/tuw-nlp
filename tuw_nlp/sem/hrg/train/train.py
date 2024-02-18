import argparse
import sys

import stanza

from tuw_nlp.common.vocabulary import Vocabulary
from tuw_nlp.sem.hrg.common.utils import parse_doc, get_ud_graph, get_pred_and_args, check_args, create_sen_dir, \
    save_as_dot
from tuw_nlp.text.utils import gen_tsv_sens


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-f", "--first", type=int)
    parser.add_argument("-l", "--last", type=int)
    parser.add_argument("-m", "--method", default="per_word", type=str, help="Either 'per_word' or 'per_arg'")
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
        sen_dir = create_sen_dir(out_dir, sen_idx)
        print(f"processing sentence {sen_idx}, writing to {sen_dir}/sen{sen_idx}.log")
        log = open(f"{sen_dir}/sen{sen_idx}.log", "w")

        parsed_doc = parse_doc(nlp, sen, sen_idx, sen_dir, log)
        ud_graph = get_ud_graph(parsed_doc)
        save_as_dot(f"{sen_dir}/sen{sen_idx}_ud.dot", ud_graph, log)

        args, pred, _ = get_pred_and_args(sen, sen_idx, log)
        arg_graphs, all_args_connected = check_args(args, log, sen_idx, ud_graph, vocab)

        if not all_args_connected:
            log.write(f"sentence {sen_idx} had unconnected arguments, skipping\n")
            continue

        if method == "per_word":
            from tuw_nlp.sem.hrg.generation.per_word import create_rules_and_graph
            create_rules_and_graph(sen_idx, ud_graph, pred, args, vocab, log, sen_dir)
        elif method == "per_arg":
            from tuw_nlp.sem.hrg.generation.per_arg import create_rules_and_graph
            create_rules_and_graph(sen_idx, ud_graph, pred, args, arg_graphs, vocab, log, sen_dir)

    vocab_fn = "vocab.txt"
    vocab.to_file(f"{vocab_fn}")
    print(f"saved vocabulary to {vocab_fn}")


if __name__ == "__main__":
    args = get_args()
    main(args.first, args.last, args.method, args.out_dir)
