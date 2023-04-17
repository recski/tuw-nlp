import argparse
import os
import sys

import stanza
from stanza.utils.conll import CoNLL
from tuw_nlp.text.pipeline import CachedStanzaPipeline, CustomStanzaPipeline


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-cd", "--cache-dir", default="cache", type=str)
    parser.add_argument("-o", "--out-file", type=str)
    parser.add_argument(
        "-p", "--processors", default="tokenize,mwt,pos,lemma,depparse", type=str
    )
    parser.add_argument("-l", "--lang", type=str)
    return parser.parse_args()


def main():
    args = get_args()

    assert os.access(args.out_file, os.W_OK) == 0, f'not writable: {args.out_file}'

    if args.lang == "de":
        nlp_pipeline = CustomStanzaPipeline(lang=args.lang, processors=args.processors)
    else:
        nlp_pipeline = stanza.Pipeline(lang=args.lang, processors=args.processors)

    nlp_cache = os.path.join(args.cache_dir, "nlp_cache.json")

    with CachedStanzaPipeline(nlp_pipeline, nlp_cache) as nlp:
        input_text = sys.stdin.read()
        doc = nlp(input_text)
        CoNLL.write_doc2conll(doc, args.out_file)


if __name__ == "__main__":
    main()
