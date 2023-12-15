from collections import defaultdict

import networkx as nx

from tuw_nlp.sem.hrg.common.utils import get_pred_arg_subgraph, write_bolinas_graph


def get_next_edges(G, root_word, pred, arg_words, log):
    next_edges = defaultdict(list)
    for _, v, e in G.edges(root_word, data=True):
        if v in pred:
            next_edges['P'].append((e['color'], v))
        elif v in arg_words:
            next_edges['A'].append((e['color'], v))
        elif v >= 1000:
            root_pos = e['color']
        else:
            next_edges['X'].append((e['color'], v))
    log.write(f"next_edges: {next_edges}\n")
    return next_edges, root_pos


def gen_subseq_rules(G, pred_edges, arg_words, pred, log):
    for lhs, edges in pred_edges.items():
        for deprel, node in edges:
            next_edges, root_pos = get_next_edges(G, node, pred, arg_words, log)

            rule = f'{lhs} -> (. :{deprel} (.'
            for non_term in next_edges:
                rule += ' ' + ' '.join(f':{non_term}$' for _ in next_edges[non_term])
            rule += f' :{root_pos} .));\n'
            yield rule

            yield from gen_subseq_rules(G, next_edges, arg_words, pred, log)


def get_initial_rule(next_edges, root_pos):
    rule = 'S -> (.'
    for lhs in next_edges:
        rule += ' ' + ' '.join(f':{lhs}$' for _ in next_edges[lhs])
    rule += f' :{root_pos} .);\n'
    return rule


def create_rules_and_graph(sen_idx, ud_graph, pred, args, vocab, log, out_dir):
    graph = get_pred_arg_subgraph(ud_graph, pred, args, vocab, log)
    write_bolinas_graph(sen_idx, graph, log, out_dir)
    root_word = next(nx.topological_sort(graph.G))
    log.write(f"root word: {root_word}\n")
    arg_words = set(w for nodes in args.values() for w in nodes)

    next_edges, root_pos = get_next_edges(graph.G, root_word, pred, arg_words, log)
    initial_rule = get_initial_rule(next_edges, root_pos)
    rules = set()
    for rule in gen_subseq_rules(graph.G, next_edges, arg_words, pred, log):
        rules.add(rule)

    with open(f"{out_dir}/sen{sen_idx}.hrg", "w") as f:
        f.write(f"{initial_rule}")
        for rule in rules:
            f.write(f"{rule}")
    log.write(f"wrote grammar to test{sen_idx}.hrg\n")