import argparse
import logging
import sys
import traceback

import stanza
from tqdm import tqdm

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
        for sen in self.nlp(text).sentences:
            fl = self.ud_fl.parse(sen, 'ud', 'fl', 'amr-sgraph-src')
            graph, root = pn_to_graph(fl)
            yield graph

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
        for i, line in tqdm(enumerate(sys.stdin)):
            try:
                fl_graphs = list(tfl(line.strip()))
            except (TypeError, IndexError, KeyError):
                traceback.print_exc()
                sys.stderr.write(f'error on line {i}: {line}')
                print('ERROR')
                continue
                # sys.exit(-1)

            print("\t".join(graph_to_pn(fl) for fl in fl_graphs))


if __name__ == "__main__":
    main()
