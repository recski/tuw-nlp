import argparse
import os

from tuw_nlp.graph.graph import Graph


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-i", "--in-dir", type=str)
    return parser.parse_args()


def main(in_dir):
    for sen_dir in os.listdir(in_dir):
        print(f"Processing sentence {sen_dir}")

        out_dir = os.path.join(in_dir, sen_dir, "matches")
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        files = os.listdir(os.path.join(in_dir, sen_dir))
        pa_graph_file = [file for file in files if file.endswith("_pa.graph")]
        assert len(pa_graph_file) == 1
        matches_file = [file for file in files if file.endswith("_matches.graph")]
        assert len(matches_file) == 1

        with open(os.path.join(in_dir, sen_dir, pa_graph_file[0])) as f:
            lines = f.readlines()
            assert len(lines) == 1
            pa_graph_str = lines[0].strip()

        pa_graph = Graph.from_bolinas(pa_graph_str)

        with open(os.path.join(in_dir, sen_dir, matches_file[0])) as f:
            matches = f.readlines()
        for i, match_str in enumerate(matches):
            match_graph = Graph.from_bolinas(match_str)

            with open(f"{out_dir}/match{i}_graph.dot", "w") as f:
                f.write(match_graph.to_dot())

            match_graph_nodes = set([n for n in match_graph.G.nodes])
            pa_graph_nodes = set([n for n in pa_graph.G.nodes])
            if match_graph_nodes.issubset(pa_graph_nodes):
                print(f"Match found: {match_str}")


if __name__ == "__main__":
    args = get_args()
    main(args.in_dir)