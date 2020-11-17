import sys

import stanza
from stanza.utils.conll import CoNLL


def depparse(line, nlp):
    doc = nlp(line.strip())
    for sen in doc.sentences:
        print("\n".join([
            "\t".join([field for field in tok])
            for tok in CoNLL.convert_dict([sen.to_dict()])[0]]))


def main():
    nlp = stanza.Pipeline(lang=sys.argv[1])
    for line in sys.stdin:
        depparse(line, nlp)
        print()


if __name__ == "__main__":
    main()
