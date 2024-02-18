import argparse
import os
from collections import Counter


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-i", "--input-dir", type=str)
    parser.add_argument("-o", "--out-dir", default="data", type=str)
    return parser.parse_args()


def main(input_dir, out_dir):
    initial_rules = Counter()
    rules = Counter()
    nts = Counter()
    for sen_dir in os.listdir(input_dir):
        filename = os.path.join(input_dir, sen_dir, f"sen{sen_dir}.hrg")
        if os.path.exists(filename):
            with open(filename) as f:
                lines = f.readlines()
            for line in lines:
                rule = line.strip()
                nt = rule[0]
                if nt == "S":
                    initial_rules[rule] += 1
                else:
                    rules[rule] += 1
                nts[nt] += 1
    with open(os.path.join(out_dir, "grammar.hrg"), "w") as f:
        write_rule(f, initial_rules, "weight", nts)
        write_rule(f, rules, "weight", nts)
    with open(os.path.join(out_dir, "grammar_stat"), "w") as f:
        write_rule(f, initial_rules, "cnt")
        write_rule(f, rules, "cnt")


def write_rule(f, rules, numeric_info=None, nts=None):
    for rule, cnt in rules.most_common():
        if not numeric_info:
            f.write(f"{rule}\n")
        elif numeric_info == "cnt":
            f.write(f"{rule}\t{cnt}\n")
        elif numeric_info == "weight" and nts:
            nt = rule[0]
            w = round(cnt / nts[nt], 2)
            if w < 0.01:
                w = 0.01
            f.write(f"{rule}\t{w}\n")


if __name__ == "__main__":
    args = get_args()
    main(args.input_dir, args.out_dir)
