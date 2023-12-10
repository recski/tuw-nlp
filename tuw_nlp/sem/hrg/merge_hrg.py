import argparse
import os
from collections import Counter


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-i", "--input-dir", type=str)
    return parser.parse_args()


def main(input_dir):
    initial_rules = Counter()
    rules = Counter()
    for filename in os.listdir(input_dir):
        if filename.endswith(".hrg"):
            with open(os.path.join(input_dir, filename)) as f:
                lines = f.readlines()
            for line in lines:
                rule = line.strip()
                if rule.startswith("S"):
                    initial_rules[rule] += 1
                else:
                    rules[rule] += 1
    with open("grammar.hrg", "w") as f:
        for rule, cnt in initial_rules.most_common():
            f.write(f"{rule}\n")
        for rule, cnt in rules.most_common():
            f.write(f"{rule}\n")
    with open("grammar_stat", "w") as f:
        for rule, cnt in initial_rules.most_common():
            f.write(f"{rule}: {cnt}\n")
        for rule, cnt in rules.most_common():
            f.write(f"{rule}: {cnt}\n")


if __name__ == "__main__":
    args = get_args()
    main(args.input_dir)
