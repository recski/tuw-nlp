import argparse
import os

from networkx.algorithms.isomorphism import DiGraphMatcher

from tuw_nlp.graph.graph import Graph
from tuw_nlp.sem.hrg.common.graphs import get_all_subgraphs, edge_matcher


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-i", "--in-dir", default="in", type=str)
    return parser.parse_args()


def add_ids(bolinas_str):
    graph_with_ids = ""
    next_id = 1
    for i, c in enumerate(bolinas_str):
        if c == '.':
            if bolinas_str[i-1] == ' ':
                graph_with_ids += f"(n{next_id})"
            else:
                graph_with_ids += f"n{next_id}"
            next_id += 1
        else:
            graph_with_ids += c
    return graph_with_ids


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

        pa_graph = Graph.from_penman(pa_graph_str, require_ids=False)

        with open(os.path.join(in_dir, sen_dir, matches_file[0])) as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                match_graph = Graph.from_penman(add_ids(line), require_ids=False)
                with open(f"{out_dir}/match{i}_graph.dot", "w") as f:
                    f.write(match_graph.to_dot())

                for H in get_all_subgraphs(pa_graph.G, len(match_graph.G.nodes)):
                    matcher = DiGraphMatcher(H, match_graph.G, edge_match=edge_matcher)
                    if matcher.subgraph_is_isomorphic():
                        print(f"Match found: {line}")


if __name__ == "__main__":
    args = get_args()
    main(args.in_dir)
