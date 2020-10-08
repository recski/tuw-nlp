from tuw_nlp.graph.utils import dummy_isi_graph, dummy_tree


DUMMY_INPUTS = {
    'de.up.ling.irtg.algebra.TreeWithAritiesAlgebra': dummy_tree,
    'de.up.ling.irtg.algebra.graph.GraphAlgebra': dummy_isi_graph
}


def get_dummy_input(input_alg):
    return DUMMY_INPUTS[input_alg]
