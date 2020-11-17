import sys

from tuw_nlp.text.segmentation import CustomStanzaPipeline
from tuw_nlp.grammar.ud_fl import UD_FL
# from tuw_nlp.graph.utils import read_alto_output


def do_ud_fl(text, nlp, ud_fl):
    sen = nlp(text).sentences[0]
    fl = ud_fl.parse(sen, 'ud', 'fl', 'amr-sgraph-src')
    # output, root = read_alto_output(fl)
    return fl


def main():
    cache_dir, cache_fn = sys.argv[1:3]
    ud_fl = UD_FL(cache_dir=cache_dir, cache_fn=cache_fn)
    nlp = CustomStanzaPipeline(processors='tokenize,pos,lemma,depparse')
    for line in sys.stdin:
        print(do_ud_fl(line.strip(), nlp, ud_fl))


if __name__ == "__main__":
    main()
