import networkx as nx
import penman as pn
from amrlib.alignments.rbw_aligner import RBWAligner
from amrlib.graph_processing.annotator import add_lemmas
from nltk.corpus import propbank
from penman import surface

from tuw_nlp.graph.graph import Graph


class AMRGraph(Graph):
    def __init__(self, pn_graph, text=None, tokens=None):

        aligned_graph = self.get_alignment(pn_graph)
        self.pn_graph = aligned_graph

        metadata = pn.decode(aligned_graph).metadata

        tokens = metadata["tokens"] if tokens is None else tokens
        text = metadata["snt"] if text is None else text
        self.lemmas = metadata["lemmas"] if "lemmas" in metadata else None

        self.counter = 0
        self.instances = propbank.instances()
        frames = [instance.roleset for instance in self.instances]
        self.frames = set(frames)

        graph = self.convert_to_networkx(aligned_graph)
        super().__init__(graph, text, tokens, type="amr")
        self.G.graph["lemmas"] = self.lemmas

    def get_alignment(self, pn_graph):
        annotated_graph = add_lemmas(pn_graph, snt_key="snt")
        aligner = RBWAligner.from_penman_w_json(annotated_graph)
        graph_string = aligner.get_graph_string()

        return graph_string

    def convert_to_networkx(self, pn_graph):
        G = nx.DiGraph()

        graph = pn.decode(pn_graph)
        alignments = surface.alignments(graph)

        # Build g.instances() => concept relations  (these are nodes)
        for t in graph.instances():
            self._add_instance(t, graph=G, alignments=alignments)
        # Build g.edges() => relations between nodes
        for t in graph.edges():
            self._add_edge(t, graph=G)
        # Build g.attributes  => relations between nodes and a constant
        for t in graph.attributes():
            self._add_attribute(t, graph=G, alignments=alignments)

        return G

    def _get_name_of_node(self, node):
        if node.startswith('"') and node.endswith('"'):
            return node[1:-1]
        elif "-" in node and node.split("-")[1].isnumeric():
            return node.split("-")[0]
        else:
            return node

    def _get_propbank_frame(self, node):
        node_to_frame = node.replace("-", ".")

        if node_to_frame in self.frames:
            return node_to_frame
        else:
            return None

    # Instances are nodes (circles with info) ie.. concept relations
    def _add_instance(self, t, graph, alignments):
        label = self._get_name_of_node(t.target)
        frame = self._get_propbank_frame(t.target)

        alignment = alignments[t] if t in alignments else None

        token_id = alignment.indices[0] if alignment else None

        graph.add_node(
            t.source, name=label, orig_name=t.target, frame=frame, token_id=token_id
        )

    # Edges are lines connecting nodes
    def _add_edge(self, t, graph):
        edge_color = ":".join(t.role.split(":")[1:])
        graph.add_edge(t.source, t.target, color=edge_color)

    # Attributes are relations (edge) connecting to a constant
    def _add_attribute(self, t, graph, alignments):
        node_id = self.get_uid()

        label = self._get_name_of_node(t.target)
        frame = self._get_propbank_frame(t.target)

        alignment = alignments[t] if t in alignments else None
        token_id = alignment.indices[0] if alignment else None

        graph.add_node(
            node_id, name=label, orig_name=t.target, frame=frame, token_id=token_id
        )
        edge_color = ":".join(t.role.split(":")[1:])
        graph.add_edge(t.source, node_id, color=edge_color)

    # Get a unique ID for naming nodes
    def get_uid(self):
        uid = "node_%d" % self.counter
        self.counter += 1
        return uid
