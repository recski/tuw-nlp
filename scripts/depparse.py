import argparse
import os
import sys

import stanza
from stanza.utils.conll import CoNLL

from tuw_nlp.text.pipeline import CachedStanzaPipeline, CustomStanzaPipeline


def depparse(line, nlp, out):
    doc = nlp(line.strip())
    for sen in doc.sentences:
        out.write(
            "\n".join(
                [
                    "\t".join([field for field in tok])
                    for tok in CoNLL.convert_dict([sen.to_dict()])[0]
                ]
            )
        )


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-cd", "--cache-dir", default="cache", type=str)
    parser.add_argument("-o", "--out-file", type=str, required=True)
    parser.add_argument("-l", "--lang", type=str, required=True)
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

    out = open(args.out_file, "w")

    with CachedStanzaPipeline(nlp_pipeline, nlp_cache) as nlp:
        for line in sys.stdin:
            depparse(line, nlp, out)
            out.write("\n\n")


if __name__ == "__main__":
    main()
