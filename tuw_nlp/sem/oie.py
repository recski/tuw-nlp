import argparse
import logging
import sys

from tqdm import tqdm


from tuw_nlp.sem.semparse import get_parser
from tuw_nlp.sem.oie_ud import ud_to_triplets
from tuw_nlp.text.preprocessor import Preprocessor


class OIE:
    def __init__(self, args):
        self.parser = get_parser(args)
        self.format = args.format
        self.preproc = Preprocessor(args.preprocessor)

    def graph_to_triplets(self, graph):
        if self.format == "ucca":
            raise Exception('ucca not yet implemented')
        if self.format == "ud":
            yield from ud_to_triplets(graph)

    def get_triplets(self, sen):
        for graph in self.parser(sen):
            yield from self.graph_to_triplets(graph)


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-f", "--format", default=None, type=str)
    parser.add_argument("-cd", "--cache-dir", default="cache", type=str)
    parser.add_argument("-cn", "--nlp-cache", default=None, type=str)
    parser.add_argument("-l", "--lang", default=None, type=str, required=True)
    parser.add_argument("-p", "--preprocessor", default=None, type=str)
    return parser.parse_args()


def main():
    logging.basicConfig(
        format="%(asctime)s : "
        + "%(module)s (%(lineno)s) - %(levelname)s - %(message)s"
    )
    logging.getLogger().setLevel(logging.WARNING)
    args = get_args()

    oie = OIE(args)

    for i, line in tqdm(enumerate(sys.stdin)):
        sen = line.strip()
        for rel, args in oie.get_triplets(sen):
            print("{0}\t{1}({2})".format(sen, rel, ", ".join(args)))


if __name__ == "__main__":
    main()
