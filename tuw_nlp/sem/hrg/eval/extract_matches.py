import argparse
import sys
from collections import defaultdict

from tuw_nlp.sem.hrg.common.utils import create_sen_dir


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-o", "--out-dir", default="out", type=str)
    return parser.parse_args()


def main(out_dir="out"):
    sen_idx = None
    matches = defaultdict(list)
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if line.startswith("Sentence"):
            sen_idx = int(line.split(' ')[-1])
        elif line.startswith("(n"):
            matches[sen_idx].append(line.strip())
    for sen_idx, matches_for_sen in matches.items():
        sen_dir = create_sen_dir(out_dir, sen_idx)
        with open(f"{sen_dir}/sen{sen_idx}_matches.graph", "w") as f:
            f.write("\n".join(matches_for_sen))


if __name__ == "__main__":
    args = get_args()
    main(args.out_dir)
