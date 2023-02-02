import os

from stanza.utils.conll import CoNLL


def gen_tikz_dep_source(words, deps, out):
    out.write(
        "\\documentclass{standalone}\n"
        "\\usepackage{tikz-dependency}\n"
        "\\begin{document}\n\n"
        "\\begin{dependency}\n"
        "\\begin{deptext}\n\n"
    )

    out.write(" \\& ".join(words) + "\\\\\n")

    out.write("\\end{deptext}\n\n")

    out.write("\n".join(deps))

    out.write("\n\\end{dependency}\n\n" "\\end{document}\n")


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


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
