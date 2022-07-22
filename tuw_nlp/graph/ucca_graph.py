from tuw_nlp.graph.graph import Graph


# Define a UCCA graph class
# This class is used to represent a UCCA graph
# It is derived from the Graph base class
class UCCAGraph(Graph):
    def __init__(self, graph=None, text=None, tokens=None):
        super().__init__(graph, text, tokens)

