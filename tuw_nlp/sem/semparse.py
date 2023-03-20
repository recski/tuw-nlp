import argparse
import logging
import os
import sys
import traceback

from graphviz import Source
from tqdm import tqdm

from tuw_nlp.common.utils import ensure_dir
from tuw_nlp.grammar.text_to_4lang import TextTo4lang
from tuw_nlp.grammar.text_to_amr import TextToAMR
from tuw_nlp.grammar.text_to_drs import TextToDRS
from tuw_nlp.grammar.text_to_ndrs import TextToNDRS
from tuw_nlp.grammar.text_to_sdp import TextToSDP
from tuw_nlp.grammar.text_to_ucca import TextToUCCA
from tuw_nlp.grammar.text_to_ud import TextToUD
from tuw_nlp.text.preprocessor import Preprocessor


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-f", "--format", default=None, type=str)
    parser.add_argument("-cd", "--cache-dir", default="cache", type=str)
    parser.add_argument("-cn", "--nlp-cache", default=None, type=str)
    parser.add_argument("-l", "--lang", default=None, type=str, required=True)
    parser.add_argument("-d", "--depth", default=0, type=int)
    parser.add_argument("-s", "--substitute", default=False, type=bool)
    parser.add_argument("-p", "--preprocessor", default=None, type=str)
    parser.add_argument("-o", "--out-dir", default="output", type=str)
    return parser.parse_args()


def get_parser(args):
    if args.format == "4lang":
        parser = TextTo4lang(args.lang, args.nlp_cache, args.cache_dir)
    elif args.format == "amr":
        parser = TextToAMR()
    elif args.format == "ndrs":
        parser = TextToNDRS(lang=args.lang)
    elif args.format == "drs":
        parser = TextToDRS(lang=args.lang)
    elif args.format == "sdp":
        parser = TextToSDP(lang=args.lang)
    elif args.format == "ucca":
        parser = TextToUCCA(lang=args.lang)
    elif args.format == "ud":
        parser = TextToUD(args.lang, args.nlp_cache, args.cache_dir)

    return parser


def main():
    logging.basicConfig(
        format="%(asctime)s : "
        + "%(module)s (%(lineno)s) - %(levelname)s - %(message)s"
    )
    logging.getLogger().setLevel(logging.WARNING)
    args = get_args()
    preproc = Preprocessor(args.preprocessor)

    parser = get_parser(args)

    dirname = os.path.join(args.out_dir, args.format)
    ensure_dir(dirname)

    for i, line in tqdm(enumerate(sys.stdin)):
        text = preproc(line.strip())
        try:
            for j, graph in enumerate(parser(text)):
                if graph is None:
                    sys.stderr.write(f"no graph returned for line {i}: {line}")
                else:
                    gv = Source(
                        graph.to_dot(),
                        filename=f"{i}_{j}",
                        directory=dirname,
                        format="png",
                    )
                    gv.render()
        except (TypeError, IndexError, KeyError):
            traceback.print_exc()
            sys.stderr.write(f"error on line {i}: {line}")
            print("ERROR")
            continue
            # sys.exit(-1)


if __name__ == "__main__":
    main()
