import argparse
import logging
import sys

import stanza

from tuw_nlp.grammar.ud_fl import UD_FL
from tuw_nlp.graph.utils import graph_to_pn, pn_to_graph
from tuw_nlp.text.pipeline import CachedStanzaPipeline, CustomStanzaPipeline


class TextTo4lang():
    def __init__(self, args):
        if args.lang == 'de':
            nlp = CustomStanzaPipeline(
                processors='tokenize,mwt,pos,lemma,depparse')
        elif args.lang == 'en':
            nlp = stanza.Pipeline(
                'en', processors='tokenize,mwt,pos,lemma,depparse')

        self.nlp = CachedStanzaPipeline(nlp, args.nlp_cache)

        self.ud_fl = UD_FL(cache_dir=args.cache_dir)

    def __call__(self, text):
        sen = self.nlp(text).sentences[0]
        fl = self.ud_fl.parse(sen, 'ud', 'fl', 'amr-sgraph-src')
        graph, root = pn_to_graph(fl)
        return graph

    def __enter__(self):
        self.nlp.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.nlp.__exit__(exc_type, exc_value, exc_traceback)


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-cd", "--cache-dir", default=None, type=str)
    parser.add_argument("-cn", "--nlp-cache", default=None, type=str)
    parser.add_argument("-l", "--lang", default=None, type=str)
    return parser.parse_args()


def main():
    logging.basicConfig(
        format="%(asctime)s : " +
        "%(module)s (%(lineno)s) - %(levelname)s - %(message)s")
    logging.getLogger().setLevel(logging.WARNING)
    args = get_args()
    with TextTo4lang(args) as tfl:
        for line in sys.stdin:
            fl = tfl(line.strip())
            print(graph_to_pn(fl))


if __name__ == "__main__":
    main()
