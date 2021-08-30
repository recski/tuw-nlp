import sys

import networkx as nx
from networkx.drawing.nx_agraph import write_dot

from tuw_nlp.graph.utils import pn_to_graph


def main():
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        G, _ = pn_to_graph(line.strip(), edge_attr='label')
        G = nx.relabel_nodes(
            G, lambda n: '{0}_{1}'.format(G.nodes[n]['name'], n))
        write_dot(G, sys.argv[1])


if __name__ == "__main__":
    main()
