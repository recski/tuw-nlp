import argparse
import os
import sys

import stanza
from stanza.utils.conll import CoNLL

from tuw_nlp.text.pipeline import CachedStanzaPipeline, CustomStanzaPipeline


def depparse(line, nlp, out, tikz_dep):
    doc = nlp(line.strip())
    for sen in doc.sentences:
        if tikz_dep:
            print_tikz_dep(sen, out)
        else:
            print_conll(sen, out)


def gen_tikz_dep_source(words, deps, out):
    out.write(
        "\\documentclass{standalone}\n"
        "\\usepackage{tikz-dependency}\n"
        "\\begin{document}\n\n"
        "\\begin{dependency}\n"
        "\\begin{deptext}\n\n"
    )

    out.write(" \\& ".join(words) + '\\\\\n')

    out.write("\\end{deptext}\n\n")

    out.write("\n".join(deps))

    out.write(
        "\n\\end{dependency}\n\n"
        "\\end{document}\n")


def print_tikz_dep(sen, out):
    words = []
    deps = []
    for word in sen.words:
        words.append(word.text)
        if word.head == 0:
            deps.append(f"\\deproot{{{word.id}}}{{ROOT}}")
        else:
            deps.append(f"\\depedge{{{word.head}}}{{{word.id}}}{{{word.deprel}}}")

    gen_tikz_dep_source(words, deps, out)


def print_conll(sen, out):
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
    parser.add_argument("-t", "--tikz-dep", default=False, action="store_true")
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
            depparse(line, nlp, out, args.tikz_dep)
            out.write("\n\n")


if __name__ == "__main__":
    main()
