import argparse
import json
import logging
import os

from tuw_nlp.graph.graph import Graph
from tuw_nlp.sem.hrg.common.utils import add_oie_data_to_nodes


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-i", "--in-dir", type=str)
    parser.add_argument("-f", "--first", type=int)
    parser.add_argument("-l", "--last", type=int)
    return parser.parse_args()


def get_range(in_dir, first, last):
    sen_dirs = sorted([int(d) for d in os.listdir(in_dir)])
    if first is None or first < sen_dirs[0]:
        first = sen_dirs[0]
    if last is None or last > sen_dirs[-1]:
        last = sen_dirs[-1]
    return range(first,  last + 1)


def main(in_dir, first, last):
    for sen_dir in get_range(in_dir, first, last):
        print(f"\nProcessing sentence {sen_dir}")
        
        sen_dir = str(sen_dir)
        out_dir = os.path.join(in_dir, sen_dir, "matches")
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        files = os.listdir(os.path.join(in_dir, sen_dir))
        graph_file = [file for file in files if file.endswith(f"sen{sen_dir}_labels.graph")]
        assert len(graph_file) == 1
        pa_graph_file = [file for file in files if file.endswith("_pa.graph")]
        assert len(pa_graph_file) == 1
        matches_file = [file for file in files if file.endswith("_matches.graph")]
        assert len(matches_file) == 1
        node_to_label_file = [file for file in files if file.endswith("node_to_label.json")]
        assert len(node_to_label_file) == 1

        with open(os.path.join(in_dir, sen_dir, graph_file[0])) as f:
            lines = f.readlines()
            assert len(lines) == 1
            graph_str = lines[0].strip()

        graph = Graph.from_bolinas(graph_str)

        with open(os.path.join(in_dir, sen_dir, node_to_label_file[0])) as f:
            node_to_label = json.load(f)

        add_oie_data_to_nodes(graph, node_to_label, node_prefix="n")

        with open(os.path.join(in_dir, sen_dir, pa_graph_file[0])) as f:
            lines = f.readlines()
            assert len(lines) == 1
            pa_graph_str = lines[0].strip()

        pa_graph = Graph.from_bolinas(pa_graph_str)

        with open(os.path.join(in_dir, sen_dir, matches_file[0])) as f:
            matches = f.readlines()
        state = None
        i = 0
        for match_str in matches:
            if match_str.strip() in ["max", "prec", "rec"]:
                state = match_str.strip()
                i = 0
                continue

            match_graph = Graph.from_bolinas(match_str)

            with open(f"{out_dir}/sen{sen_dir}_match_{state}_{i}.dot", "w") as f:
                f.write(match_graph.to_dot())

            match_graph_nodes = set([n for n in match_graph.G.nodes])
            match_graph_edges = set([(u, v, d["color"]) for (u, v, d) in match_graph.G.edges(data=True)])
            pa_graph_nodes = set([n for n in pa_graph.G.nodes])
            pa_graph_edges = set([(u, v, d["color"]) for (u, v, d) in pa_graph.G.edges(data=True)])

            print(f"Match {state} {i}")
            print(f"Node matches: {len(match_graph_nodes & pa_graph_nodes)}/{len(pa_graph_nodes)}")
            print(f"Edge matches: {len(match_graph_edges & pa_graph_edges)}/{len(pa_graph_edges)}")

            with open(f"{out_dir}/sen{sen_dir}_match_{state}_{i}_graph.dot", "w") as f:
                f.write(graph.to_dot(marked_nodes=match_graph_nodes))

            i += 1


if __name__ == "__main__":
    logging.getLogger('penman').setLevel(logging.ERROR)

    args = get_args()
    main(args.in_dir, args.first, args.last)