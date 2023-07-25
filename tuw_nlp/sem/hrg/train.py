import sys
from collections import defaultdict

import penman as pn
import stanza
from stanza.utils.conll import CoNLL

from tuw_nlp.common.vocabulary import Vocabulary
from tuw_nlp.graph.graph import UnconnectedGraphError
from tuw_nlp.graph.ud_graph import UDGraph
from tuw_nlp.text.utils import gen_tsv_sens


def get_pred_graph_bolinas(pred_graph, arg_roots):
    nodes = {}
    pn_edges = []
    root_nodes, non_root_nodes = set(), set()
    arg_roots_to_i = {node: i for i, node in enumerate(arg_roots)}
    # print("arg roots:", arg_roots_to_i)
    for u, v, e in pred_graph.G.edges(data=True):
        # print("u, v, e:", u, v, e)
        if v in root_nodes:
            root_nodes.remove(v)
        non_root_nodes.add(v)
        if u not in non_root_nodes:
            root_nodes.add(u)

        for node in u, v:
            if node not in nodes:
                nodes[node] = f"n{node}."

        if v in arg_roots_to_i:
            arg_index = arg_roots_to_i[v]
            if u in arg_roots_to_i:
                """This is the case when an argument connects to the predicate through another argument"""
                pn_edges.append(
                    (f"A{arg_roots_to_i[u]}.", e["color"], f"A{arg_index}.")
                )
            else:
                pn_edges.append((nodes[u], e["color"], f"A{arg_index}."))
            pn_edges.append((f"A{arg_index}.", "A$", ""))

        elif u not in arg_roots_to_i:
            pn_edges.append((nodes[u], e["color"], nodes[v]))

    # print("pn_edges:", pn_edges)

    assert len(root_nodes) == 1, f"graph has no unique root: {root_nodes}"
    top_node = root_nodes.pop()

    G = pn.Graph(pn_edges)
    return pn.encode(G, top=f"n{top_node}.", indent=0).replace("\n", " ")


def main():
    nlp = stanza.Pipeline(
        lang="en",
        processors="tokenize,mwt,pos,lemma,depparse",
        tokenize_pretokenized=True,
    )
    vocab = Vocabulary(first_id=1000)
    for sen_idx, sen in enumerate(gen_tsv_sens(sys.stdin)):
        parsed_doc = nlp(" ".join(t[1] for t in sen))
        parsed_sen = parsed_doc.sentences[0]
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
        # print(ud_graph.to_penman())
        # with open(f"test{sen_idx}_orig.dot", 'w') as f:
        #     f.write(ud_graph.to_dot())
        CoNLL.write_doc2conll(parsed_doc, f"test{sen_idx}.conll")
        print(f"wrote parse to test{sen_idx}.conll")

        agraphs_bolinas, arg_roots = [], []
        for arg, nodes in args.items():
            try:
                agraph = ud_graph.subgraph(nodes).pos_edge_graph(vocab)
            except UnconnectedGraphError:
                print(f'unconnected argument ({nodes}) in sentence {sen_idx}, skipping')
                continue
            bolinas_str, arg_root = agraph.to_bolinas(return_root=True)
            agraphs_bolinas.append(bolinas_str)
            arg_roots.append(arg_root)
        
        if len(agraphs_bolinas) == 0:
            print(f'sentence {sen_idx} has no arguments, skipping')
            continue

        pred_graph = ud_graph.subgraph(
            pred + arg_roots, handle_unconnected="shortest_path"
        ).pos_edge_graph(vocab)
        pred_graph_bolinas = get_pred_graph_bolinas(pred_graph, arg_roots)

        with open(f"test{sen_idx}.hrg", "w") as f:
            f.write(f"S -> {pred_graph_bolinas}; 1.0 # 1\n")
            for i, agraph_bolinas in enumerate(agraphs_bolinas):
                f.write(f"A -> {agraph_bolinas}; 1.0 # {i+2}\n")
        print(f"wrote grammar to test{sen_idx}.hrg")

        idx_to_keep = [n for nodes in args.values() for n in nodes] + pred
        pruned_graph_bolinas = (
            ud_graph.subgraph(idx_to_keep, handle_unconnected="shortest_path")
            .pos_edge_graph(vocab)
            .to_bolinas()
        )
        with open(f"test{sen_idx}.graph", "w") as f:
            f.write(f"{pruned_graph_bolinas}\n")
        print(f"wrote graph to test{sen_idx}.graph")

        # print(graph.to_penman(name_attr='upos'))
    vocab_fn = "vocab.txt"
    vocab.to_file(f"{vocab_fn}")
    print(f"saved vocabulary to {vocab_fn}")


if __name__ == "__main__":
    main()
