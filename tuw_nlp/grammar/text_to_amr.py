import amrlib

from tuw_nlp.graph.amr_graph import AMRGraph


class TextToAMR:
    def __init__(self):
        self.amr_stog = amrlib.load_stog_model()

    def __call__(self, text):
        pn_graphs = self.amr_stog.parse_sents([text])

        amr_graph = AMRGraph(pn_graphs[0], text)

        yield amr_graph
