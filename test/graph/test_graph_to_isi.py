from tuw_nlp.graph.utils import graph_to_isi, read_alto_output


def test_plain_graph_to_isi():
    graph_string = "(u_1<root> / ueberschreiten  :0 (u_3 / NEG)  :2 (u_6 / m  :0 (u_9 / X6COMMA5))  :0 (u_12 / PER)  :1 (u_15 / Gebaeudehoehe))"  # noqa
    graph, root = read_alto_output(graph_string)
    new_string = graph_to_isi(
        graph, ud=False, root_id=root, algebra='graph', preprocess=False)
    assert graph_string == new_string


if __name__ == "__main__":
    test_plain_graph_to_isi()
