import sys
from collections import defaultdict

import penman as pn
import stanza

from tuw_nlp.common.vocabulary import Vocabulary
from tuw_nlp.graph.ud_graph import UDGraph
from tuw_nlp.text.utils import gen_tsv_sens


def get_pred_graph_bolinas(pred_graph, graph, args):
    nodes = {}
    pn_edges = []
    root_nodes, non_root_nodes = set(), set()
    for u, v, e in pred_graph.G.edges(data=True):
        if v in root_nodes:
            root_nodes.remove(v)
        non_root_nodes.add(v)
        if u not in non_root_nodes:
            root_nodes.add(u)

        for node in u, v:
            if node not in nodes:
                nodes[node] = f"n{node}."
        pn_edges.append((nodes[u], f':{e["color"]}', nodes[v]))

    assert len(root_nodes) == 1, f"graph has no unique root: {root_nodes}"
    top_node = root_nodes.pop()

    arg_nodes_to_arg_i = {node: i for i, nodes in args.items() for node in nodes}
    for node in pred_graph.G.nodes:
        for _, v, d in graph.G.out_edges(node, data=True):
            if v in arg_nodes_to_arg_i:
                arg_index = arg_nodes_to_arg_i[v]
                pn_edges.append((nodes[node], d["color"], f"{arg_index}."))
                pn_edges.append((f"{arg_index}.", "A$", ""))

    G = pn.Graph(pn_edges)
    return pn.encode(G, top=f"n{top_node}.", indent=0).replace("\n", " ")


def main():
    nlp = stanza.Pipeline(
        lang="en",
        processors="tokenize,mwt,pos,lemma,depparse",
        tokenize_pretokenized=True,
    )
    vocab = Vocabulary(first_id=1000)
    for sen in gen_tsv_sens(sys.stdin):
        parsed_sen = nlp(" ".join(t[1] for t in sen)).sentences[0]
        args = defaultdict(list)
        pred = []
        for i, tok in enumerate(sen):
            label = tok[7].split("-")[0]
            if label == "O":
                continue
            elif label == "P":
                pred.append(i + 1)
                continue
            args[label].append(i + 1)

        ud_graph = UDGraph(parsed_sen)
        graph = ud_graph.pos_edge_graph(vocab)
            
        pred_graph = ud_graph.subgraph(pred).pos_edge_graph(vocab)
        pred_graph_bolinas = get_pred_graph_bolinas(pred_graph, graph, args)
        
        agraphs_bolinas = []
        for arg, nodes in args.items():
            agraph = ud_graph.subgraph(nodes).pos_edge_graph(vocab)
            agraphs_bolinas.append(agraph.to_bolinas())
        
        with open('test.hrg', 'w') as f:
            f.write(f"S -> {pred_graph_bolinas}; 1.0 # 1\n")
            for i, agraph_bolinas in enumerate(agraphs_bolinas):
                f.write(f"A -> {agraph_bolinas}; 1.0 # {i+2}\n")
        print("wrote grammar to test.hrg")

        graph_bolinas = graph.to_bolinas()
        with open('test.graph', 'w') as f:
            f.write(f'{graph_bolinas}\n')
        print("wrote graph to test.graph")

        # print(graph.to_penman(name_attr='upos'))
    vocab_fn = "vocab.txt"
    vocab.to_file(f"{vocab_fn}")
    print(f"saved vocabulary to {vocab_fn}")


if __name__ == "__main__":
    main()
