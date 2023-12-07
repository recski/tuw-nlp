import argparse
import sys
from collections import defaultdict

import stanza
from stanza.utils.conll import CoNLL

from tuw_nlp.common.vocabulary import Vocabulary
from tuw_nlp.graph.graph import UnconnectedGraphError
from tuw_nlp.graph.ud_graph import UDGraph
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
        print(f"processing sentence {sen_idx}, writing to {out_dir}/test{sen_idx}.log")
        log = open(f"{out_dir}/test{sen_idx}.log", "w")
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
        with open(f"{out_dir}/test{sen_idx}_ud.dot", "w") as f:
            f.write(ud_graph.to_dot())
        log.write(f"test{sen_idx} pred: {pred}, args: {args}\n")
        CoNLL.write_doc2conll(parsed_doc, f"{out_dir}/test{sen_idx}.conll")
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

        if method == "per_word":
            from tuw_nlp.sem.hrg.rule_gen.per_word import create_rules_and_graph
            create_rules_and_graph(sen_idx, ud_graph, pred, args, vocab, log, out_dir)
        elif method == "per_arg":
            from tuw_nlp.sem.hrg.rule_gen.per_arg import create_rules_and_graph
            create_rules_and_graph(sen_idx, ud_graph, pred, args, agraphs, vocab, log, out_dir)

    vocab_fn = "vocab.txt"
    vocab.to_file(f"{vocab_fn}")
    print(f"saved vocabulary to {vocab_fn}")


if __name__ == "__main__":
    args = get_args()
    main(args.first, args.last, args.method, args.out_dir)
