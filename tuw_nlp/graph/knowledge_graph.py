import networkx as nx
import pandas as pd
import re
import nltk
import stanza
from nltk.corpus import wordnet as wn
from graphviz import Source
from tuw_nlp.text.pipeline import CachedStanzaPipeline
import os
import conceptnet_lite
from conceptnet_lite import Label, edges_between
from peewee import DoesNotExist
from pywsd.lesk import simple_lesk, cosine_lesk, adapted_lesk, original_lesk

nltk.download('wordnet')
if not os.path.exists("conceptnet/conceptnet.db"):
    answer = input("Would you like to download ConceptNet? It might take more than an hour. (Yes/no)")
    if not answer.lower().startswith('n'):
        use_conceptnet = True
        conceptnet_lite.connect("conceptnet/conceptnet.db", db_download_url=None)
    else:
        use_conceptnet = False
else:
    use_conceptnet = True
    conceptnet_lite.connect("conceptnet/conceptnet.db")


class KnowledgeNode:
    def __init__(self, text, lemma, synset, concept):
        self.text = text
        self.lemma = lemma
        self.synset = synset
        self.concept = concept
        self.antonym = self.get_antonym()

    def get_antonym(self):
        if 'antonym' in self.__dict__:
            return self.antonym
        if self.synset is None:
            return None
        lemma = self.synset.lemmas()
        if len(lemma) == 0:
            return None
        antonym = lemma[0].antonyms()
        if len(antonym) == 0:
            return None
        return antonym[0].synset()

    def concept_connection(self, other):
        if self.concept is not None and other.concept is not None and self.synset is not None:
            return [e for e in edges_between(self.concept, other.concept)]
        else:
            return []

    def reg_match(self, text):
        text_match = re.findall(text.lower(), self.text.lower()) + re.findall(text.lower(), self.lemma.lower())
        if len(text_match) == 0:
            return False
        return True

    def similarity(self, other):
        if self.synset is None or other.synset is None:
            return 1 if self.text == other.text or self.lemma == other.lemma else 0
        similarity = self.synset.wup_similarity(other.synset)
        if self.antonym is not None:
            antonym_similarity = self.antonym.wup_similarity(other.synset)
            if antonym_similarity > similarity:
                return -antonym_similarity
        return similarity

    def __str__(self):
        if self.synset is None:
            return self.text
        return self.synset._name

    def __eq__(self, other):
        if isinstance(other, str):
            return self.reg_match(other)
        elif isinstance(other, KnowledgeNode):
            text_match = self.reg_match(other.text)
            if text_match:
                return True
            syn_similarity_rate = 0
            concept_weight = 0 if self.concept != other.concept else 1  # There are no concept edges between the same concepts
            if self.synset is not None and other.synset is not None:
                syn_similarity_rate = self.similarity(other)
            if self.concept is not None and other.concept is not None:
                concept_connections = self.concept_connection(other)
                antonyms = [e for e in concept_connections if e.relation.name == "antonym"] + \
                           [e for e in concept_connections if e.relation.name == "distinct_from"]
                related = [e for e in concept_connections if e.relation.name == "is_a"] + \
                          [e for e in concept_connections if e.relation.name == "related_to"]
                if len(antonyms) > 0:
                    concept_weight = -1
                elif len(concept_connections) != 0:
                    concept_weight = len(related) / len(concept_connections)
            return (syn_similarity_rate + concept_weight) / 2 >= 0.5

    def __hash__(self):
        return hash(self.lemma) + hash(self.concept) + hash(self.synset)


class KnowledgeGraph:
    def __init__(self, graph=None, text=None, pipeline=None, lang="en"):
        self.pos = {'ADJ': wn.ADJ, 'ADV': wn.ADV, 'PART': wn.ADV, 'NOUN': wn.NOUN,
                    'PROPN': wn.NOUN, 'VERB': wn.VERB}
        self.lesk_pos = {'ADJ': 'a', 'ADV': 's', 'PART': 's', 'NOUN': 'n',
                         'PROPN': 'n', 'VERB': 'v'}
        self.parser = pipeline if pipeline is not None \
            else CachedStanzaPipeline(stanza.Pipeline(lang, processors='tokenize,mwt,pos,lemma,depparse'), "cache")
        self.lang = lang
        self.text = text
        self.G = graph
        if self.text is not None and self.G is None:
            self.G = nx.MultiGraph()
            self.parse_graph()
            self.connect_sentence_graphs()

    def parse_graph(self):
        with self.parser:
            ud_parse = self.parser.parse(self.text)
            for sent_id, sent in enumerate(ud_parse.sentences):
                for word in sent.words:
                    concept = None
                    synset = None
                    try:
                        concept = Label.get(text=word.lemma, language=self.lang).concepts
                    except DoesNotExist:
                        pass
                    if word.pos in self.pos:
                        synset = wn.synsets(word.lemma, pos=self.pos[word.pos])
                        if len(synset) > 1:
                            # TODO: how to find the best???
                            ss = simple_lesk(self.text, word.text, pos=self.lesk_pos[word.pos])
                            #sso = original_lesk(self.text, word.text)
                            #ssa = adapted_lesk(self.text, word.text, pos='a')
                            #ssc = cosine_lesk(self.text, word.text, pos='a')
                            synset = ss
                        elif len(synset) == 1:
                            synset = synset[0]
                        else:
                            synset = None
                    self.G.add_node((sent_id, word.id), data=KnowledgeNode(word.text, word.lemma, synset, concept))
                for dep in sent.dependencies:
                    if dep[0].id != 0:
                        self.G.add_edge((sent_id, dep[0].id), (sent_id, dep[2].id), data={"type": "dep", "rel": dep[1]})

    def connect_sentence_graphs(self):
        for node, node_data in self.G.nodes(data=True):
            for other_node, other_node_data in self.G.nodes(data=True):
                if node[0] != other_node[0]:
                    concept_connections = node_data["data"].concept_connection(other_node_data["data"])
                    for concept_connection in concept_connections:
                        self.G.add_edge(node, other_node, data={"type": "concept",
                                                                "rel": concept_connection.relation.name})

    def similarity(self, other, with_edges=False):
        if not with_edges:
            overlap = len(set([data["data"] for (_, data) in self.G.nodes(data=True)]) & \
                          set([data["data"] for (_, data) in other.G.nodes(data=True)]))
            return overlap / len(set([data["data"] for (_, data) in self.G.nodes(data=True)]))
        else:
            edge_overlap = set([(self.G.nodes(data=True)[f]["data"], self.G.nodes(data=True)[t]["data"],
                                 data["data"]["rel"]) for (f, t, data) in self.G.edges(data=True)]) & \
                           set([(other.G.nodes(data=True)[f]["data"], other.G.nodes(data=True)[t]["data"],
                                 data["data"]["rel"]) for (f, t, data) in other.G.edges(data=True)])
            return len(edge_overlap) / len(self.G.edges)

    @staticmethod
    def d_clean(string):
        s = string
        for c in '\\=@-,\'".!:;<>/{}[]()#^?':
            s = s.replace(c, '_')
        s = s.replace('$', '_dollars').replace('%', '_percent').replace('|', ' ').replace('*', ' ')
        if s == '#':
            s = '_number'
        keywords = ("graph", "node", "strict", "edge")
        if re.match('^[0-9]', s) or s in keywords:
            s = "X" + s
        return s

    def to_dot(self):
        show_graph = self.G.copy()
        #show_graph.remove_nodes_from(list(nx.isolates(show_graph)))
        lines = [u'digraph finite_state_machine {', '\tdpi=70;']
        node_id = {n: i for (i, n) in enumerate(show_graph.nodes)}
        node_lines = []
        for node, n_data in show_graph.nodes(data=True):
            printname = self.d_clean(str(n_data['data']))
            node_line = u'\t{0} [shape = circle, label = "{1}"];'.format(node_id[node], printname).replace('-', '_')
            node_lines.append(node_line)
        lines += sorted(node_lines)
        edge_lines = []
        for u, v, edata in show_graph.edges(data=True):
            if edata['data']['type'] == "dep":
                edge_lines.append(u'\t{0} -> {1} [ label = "{2}", color = "green"];'.format(node_id[u], node_id[v],
                                                                                            edata['data']['rel']))
            else:
                edge_lines.append(u'\t{0} -> {1} [ label = "{2}", color = "blue"];'.format(node_id[u], node_id[v],
                                                                                           edata['data']['rel']))
        lines += sorted(edge_lines)
        lines.append('}')
        return u'\n'.join(lines)
