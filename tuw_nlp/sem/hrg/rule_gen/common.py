def write_graph(sen_idx, pred_arg_graph, log):
    pruned_graph_bolinas = pred_arg_graph.to_bolinas()
    with open(f"out/test{sen_idx}_graph.dot", "w") as f:
        f.write(pred_arg_graph.to_dot())
    with open(f"out/test{sen_idx}.graph", "w") as f:
        f.write(f"{pruned_graph_bolinas}\n")
    log.write(f"wrote graph to test{sen_idx}.graph\n")


def get_pred_arg_subgraph(ud_graph, pred, args, vocab, log):
    idx_to_keep = [n for nodes in args.values() for n in nodes] + pred
    log.write(f"idx_to_keep: {idx_to_keep}\n")
    return ud_graph.subgraph(idx_to_keep, handle_unconnected="shortest_path").pos_edge_graph(vocab)