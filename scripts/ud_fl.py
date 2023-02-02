import argparse
import os
import sys

import stanza

from tuw_nlp.text.pipeline import CachedStanzaPipeline, CustomStanzaPipeline
from tuw_nlp.grammar.ud_fl import UD_FL

# from tuw_nlp.graph.utils import read_alto_output


def do_ud_fl(text, nlp, ud_fl):
    sen = nlp(text).sentences[0]
    fl = ud_fl.parse(sen, "ud", "fl", "amr-sgraph-src")
    # output, root = read_alto_output(fl)
    return fl


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-cd", "--cache-dir", default="cache", type=str)
    parser.add_argument("-l", "--lang", type=str)
    return parser.parse_args()


def main():
    args = get_args()
    if args.lang == "de":
        nlp_pipeline = CustomStanzaPipeline(
            processors="tokenize,mwt,pos,lemma,depparse"
        )
    elif args.lang == "en":
        nlp_pipeline = stanza.Pipeline(
            lang="en", processorts="tokenize,mwt,pos,lemma,depparse"
        )

    nlp_cache = os.path.join(args.cache_dir, "nlp_cache.json")

    ud_fl = UD_FL(lang=args.lang, cache_dir=args.cache_dir)

    with CachedStanzaPipeline(nlp_pipeline, nlp_cache) as nlp:
        for line in sys.stdin:
            print(do_ud_fl(line.strip(), nlp, ud_fl))


if __name__ == "__main__":
    main()
