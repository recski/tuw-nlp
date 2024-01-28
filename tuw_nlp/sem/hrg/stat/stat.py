import sys
from collections import defaultdict


def main():
    sen_idx = None
    stat = defaultdict(list)
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if line.startswith("Sentence"):
            sen_idx = int(line.split(' ')[-1])
        elif line.startswith("IOError"):
            stat["unconnected_arg"].append(sen_idx)
        elif "No derivations." in line:
            stat["no_derivation"].append(sen_idx)
        elif line.endswith("#1"):
            stat["success"].append(sen_idx)

    success = len(stat["success"])
    no_derivation = len(stat["no_derivation"])
    unconnected = len(stat["unconnected_arg"])
    all_sen = success + no_derivation + unconnected
    print(f"{stat}\n")
    print(f"success: {success}/{all_sen}")
    print(f"no_derivation: {no_derivation}/{all_sen}")
    print(f"unconnected: {unconnected}/{all_sen}")


if __name__ == "__main__":
    main()
