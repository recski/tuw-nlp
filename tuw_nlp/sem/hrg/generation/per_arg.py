import re

import networkx as nx
import penman as pn

from tuw_nlp.sem.hrg.common.utils import save_bolinas_str, get_pred_arg_subgraph, save_as_dot


def get_pred_graph(ud_graph, pred, args, log):

    G_u = ud_graph.G.to_undirected()

    closest_nodes = {
        arg: min(
            nodes,
            key=lambda v: min(nx.shortest_path_length(G_u, v, u) for u in pred),
        )
        for arg, nodes in args.items()
    }

    log.write(f"closest nodes: {closest_nodes}\n")
    pred_graph = ud_graph.subgraph(
        pred + list(closest_nodes.values()), handle_unconnected="shortest_path"
    )
    return pred_graph, closest_nodes


def get_pred_graph_bolinas(pred_graph, arg_anchors, args, log, keep_node_labels=True):
    nodes = {}
    pn_edges = []
    in_degrees, out_degrees = {}, {}
    arg_anchors_to_node = {}
    arg_anchors_to_arg_nodes = {}
    for arg, node in arg_anchors.items():
        arg_node = f"{arg}."
        arg_anchors_to_node[node] = arg_node
        in_degrees[arg_node] = 0
        out_degrees[arg_node] = 0
        arg_anchors_to_arg_nodes[node] = set(args[node])

    log.write(f"arg anchors: {arg_anchors_to_node}\n")
    log.write(f"arg_anchors_to_arg_nodes: {arg_anchors_to_arg_nodes}\n")

    anchor_nodes_handled = set()
    tail_anchors = set()

    for u, v, e in pred_graph.G.edges(data=True):
        log.write(f"{u} -{e['color']}-> {v}\n")

        # keep track of node labels and degrees
        for node in u, v:
            if node not in nodes:
                nodes[node] = f"n{node}."
                in_degrees[f"n{node}."] = 0
                out_degrees[f"n{node}."] = 0

        # discard leafs of args
        if u in arg_anchors_to_node and v >= 1000:
            continue

        src = arg_anchors_to_node.get(u, nodes[u])
        tgt = arg_anchors_to_node.get(v, nodes[v])

        if (
            v in arg_anchors_to_node
            and v not in anchor_nodes_handled
            and u not in arg_anchors_to_arg_nodes[v]
        ):
            pn_edges.append((tgt, "A$", ""))
            out_degrees[tgt] += 1
            anchor_nodes_handled.add(v)

            pn_edges.append((src, e["color"], tgt))
            in_degrees[tgt] += 1
            out_degrees[src] += 1

        elif (
            u in arg_anchors_to_node
            and u not in anchor_nodes_handled
            and v not in arg_anchors_to_arg_nodes[u]
        ):
            log.write(f"adding reverse arg edge based on this edge: {u}, {v}, {e}\n")
            pn_edges.append((src, "A$", nodes[u]))
            pn_edges.append((nodes[u], e["color"], tgt))
            out_degrees[src] += 1
            out_degrees[nodes[u]] += 1
            in_degrees[tgt] += 1
            in_degrees[nodes[u]] += 1
            anchor_nodes_handled.add(u)
            tail_anchors.add(u)

        else:
            pn_edges.append((src, e["color"], tgt))
            in_degrees[tgt] += 1
            out_degrees[src] += 1

    log.write(f"pn_edges: {pn_edges}\n")

    # find the unique root node so we can draw the graph
    root_nodes = set(
        node
        for node, count in in_degrees.items()
        if count == 0 and out_degrees[node] > 0
    )
    assert len(root_nodes) == 1, f"graph has no unique root: {root_nodes}"
    top_node = root_nodes.pop()

    G = pn.Graph(pn_edges)

    bolinas_str = pn.encode(G, top=top_node, indent=0).replace("\n", " ")

    if not keep_node_labels:
        bolinas_str = re.sub(r"n[0-9]*\.", ".", bolinas_str)
    return bolinas_str, tail_anchors


def create_rules_and_graph(sen_idx, ud_graph, pred, args, arg_graphs, vocab, log, out_dir):

    pred_graph_ud, arg_anchors = get_pred_graph(ud_graph, pred, args, log)
    pred_graph = pred_graph_ud.pos_edge_graph(vocab)

    with open(f"out/test{sen_idx}_pred.dot", "w") as f:
        f.write(pred_graph.to_dot())
    pred_graph_bolinas, tail_anchors = get_pred_graph_bolinas(
        pred_graph, arg_anchors, args, log, keep_node_labels=False
    )
    log.write(f"tail_anchors: {tail_anchors}\n")

    if len(tail_anchors) != 0:
        print("tail_anchors:", tail_anchors)

    agraphs_bolinas = []
    for arg, agraph in arg_graphs.items():
        anchor = arg_anchors[arg]
        ext_node = anchor if anchor in tail_anchors else None
        agraphs_bolinas.append(
            agraph.to_bolinas(ext_node=ext_node, keep_node_ids=False)
        )

    with open(f"{out_dir}/sen{sen_idx}.hrg", "w") as f:
        f.write(f"S -> {pred_graph_bolinas};\n")
        for i, agraph_bolinas in enumerate(agraphs_bolinas):
            f.write(f"A -> {agraph_bolinas};\n")
    log.write(f"wrote grammar to test{sen_idx}.hrg\n")

    bolinas_graph = get_pred_arg_subgraph(ud_graph, pred, args, vocab, log)
    save_as_dot(f"{out_dir}/sen{sen_idx}_graph.dot", bolinas_graph, log)
    save_bolinas_str(f"{out_dir}/sen{sen_idx}.graph", bolinas_graph, log)
