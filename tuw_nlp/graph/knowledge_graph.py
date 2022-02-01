from git import base
import networkx as nx
import pandas as pd
import re
import nltk
import stanza
from nltk.corpus import wordnet as wn
from tuw_nlp.text.pipeline import CachedStanzaPipeline
import os
import conceptnet_lite
from conceptnet_lite import Label, Concept, edges_between
from conceptnet_lite.db import RelationName
from pywsd.lesk import simple_lesk, cosine_lesk, adapted_lesk, original_lesk


basepath = os.path.dirname(__file__)
nltk.download('wordnet')
if not os.path.exists(os.path.join(basepath, "conceptnet/conceptnet.db")):
    answer = input("Would you like to download ConceptNet? It might take more than an hour. (Yes/no)")
    if not answer.lower().startswith('n'):
        use_conceptnet = True
        conceptnet_lite.connect(os.path.join(basepath, "conceptnet/conceptnet.db"), db_download_url=None)
    else:
        use_conceptnet = False
else:
    use_conceptnet = True
    conceptnet_lite.connect(os.path.join(basepath, "conceptnet/conceptnet.db"))


class KnowledgeNode(str):

    # We need this because penman will not recognise it as atomic otherwise
    def __new__(cls, *args, **kwargs):
        obj = super(KnowledgeNode, cls).__new__(cls, args[0])
        return obj

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
        if text.lower() == self.text.lower():
            return True
        text_match = re.findall(text.lower(), self.text.lower()) + re.findall(text.lower(), self.lemma.lower())
        if len(text_match) == 0:
            return False
        return True

    def similarity(self, other):
        if self.synset is None or other.synset is None:
            return 1 if self.text == other.text or self.lemma == other.lemma else 0
        # As per issue: https://github.com/alvations/pywsd/issues/54
        similarity = wn.synset(self.synset.name()).wup_similarity(wn.synset(other.synset.name()))
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
        if isinstance(other, KnowledgeNode):
            text_match = self.reg_match(other.text)
            if text_match:
                return True
            syn_similarity_rate = 0
            concept_weight = 0 if self.concept != other.concept else 1  # There are no concept edges between the same concepts
            if self.synset is not None and other.synset is not None:
                syn_similarity_rate = wn.synset(self.synset.name()).wup_similarity(wn.synset(other.synset.name()))
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
        elif isinstance(other, str):
            if '.' in other and self.synset is not None:
                try:
                    synset = wn.synset(other)
                    return synset.wup_similarity(wn.synset(self.synset.name())) >= 0.5
                except ValueError:
                    pass
            return self.reg_match(other)

    def __hash__(self):
        if self.concept is not None:
            return hash(self.lemma) + hash(tuple(self.concept)) + hash(self.synset)
        return hash(self.lemma) + hash(self.concept) + hash(self.synset)

    def __setstate__(self, state):
        self.text = state["text"]
        self.lemma = state["lemma"]
        self.synset = None if state["synset"] is None else wn.synset(state["synset"])
        self.antonym = None if state["antonym"] is None else wn.synset(state["antonym"])
        self.concept = None if state["concept"] is None else [Concept.get_by_id(concept) for concept in state["concept"]]
    
    def __getstate__(self):
        return {
            "text": self.text,
            "lemma": self.lemma,
            "synset": None if self.synset is None else self.synset.name(),
            "antonym": None if self.antonym is None else self.antonym.name(),
            "concept": None if self.concept is None else [c.id for c in self.concept]
        }


class KnowledgeGraph:
    def __init__(self, graph=None, text=None, pipeline=None, lang="en"):
        self.wn_lexnames = ["adj.all", # 	all adjective clusters
                            "adj.pert", # 	relational adjectives (pertainyms)
                            "adv.all", #	all adverbs
                            "noun.Tops", # 	unique beginner for nouns
                            "noun.act", # 	nouns denoting acts or actions
                            "noun.animal", # 	nouns denoting animals
                            "noun.artifact", # 	nouns denoting man-made objects
                            "noun.attribute", # 	nouns denoting attributes of people and objects
                            "noun.body", # 	nouns denoting body parts
                            "noun.cognition", # 	nouns denoting cognitive processes and contents
                            "noun.communication", # 	nouns denoting communicative processes and contents
                            "noun.event", # 	nouns denoting natural events
                            "noun.feeling", # 	nouns denoting feelings and emotions
                            "noun.food", # 	nouns denoting foods and drinks
                            "noun.group", # 	nouns denoting groupings of people or objects
                            "noun.location", # 	nouns denoting spatial position
                            "noun.motive", # 	nouns denoting goals
                            "noun.object", # 	nouns denoting natural objects (not man-made)
                            "noun.person", # 	nouns denoting people
                            "noun.phenomenon", # 	nouns denoting natural phenomena
                            "noun.plant", # 	nouns denoting plants
                            "noun.possession", # 	nouns denoting possession and transfer of possession
                            "noun.process", # 	nouns denoting natural processes
                            "noun.quantity", # 	nouns denoting quantities and units of measure
                            "noun.relation", # 	nouns denoting relations between people or things or ideas
                            "noun.shape", # 	nouns denoting two and three dimensional shapes
                            "noun.state", # 	nouns denoting stable states of affairs
                            "noun.substance", # 	nouns denoting substances
                            "noun.time", # 	nouns denoting time and temporal relations
                            "verb.body", # 	verbs of grooming, dressing and bodily care
                            "verb.change", # 	verbs of size, temperature change, intensifying, etc.
                            "verb.cognition", # 	verbs of thinking, judging, analyzing, doubting
                            "verb.communication", # 	verbs of telling, asking, ordering, singing
                            "verb.competition", # 	verbs of fighting, athletic activities
                            "verb.consumption", # 	verbs of eating and drinking
                            "verb.contact", # 	verbs of touching, hitting, tying, digging
                            "verb.creation", # 	verbs of sewing, baking, painting, performing
                            "verb.emotion", # 	verbs of feeling
                            "verb.motion", # 	verbs of walking, flying, swimming
                            "verb.perception", # 	verbs of seeing, hearing, feeling
                            "verb.possession", # 	verbs of buying, selling, owning
                            "verb.social", # 	verbs of political and social activities and events
                            "verb.stative", # 	verbs of being, having, spatial relations
                            "verb.weather", # 	verbs of raining, snowing, thawing, thundering
                            "adj.ppl"] # 	participial adjectives
        self.pos = {'ADJ': wn.ADJ, 'ADV': wn.ADV, 'PART': wn.ADV, 'NOUN': wn.NOUN,
                    'PROPN': wn.NOUN, 'VERB': wn.VERB}
        self.lesk_pos = {'ADJ': 'a', 'ADV': 's', 'PART': 's', 'NOUN': 'n',
                         'PROPN': 'n', 'VERB': 'v'}
        self.concept_pos = {'ADJ': 'a', 'ADV': 'r', 'NOUN': 'n', 'VERB': 'v'}
        self.parser = pipeline if pipeline is not None \
            else CachedStanzaPipeline(stanza.Pipeline(lang, processors='tokenize,mwt,pos,lemma,depparse'), "cache")
        self.lang = lang
        self.text = text
        self.G = graph
        if self.text is not None and self.G is None:
            self.G = nx.DiGraph()
            self.parse_graph()
            self.connect_sentence_graphs()

    def parse_graph(self):
        with self.parser:
            ud_parse = self.parser.parse(self.text)
            for sent_id, sent in enumerate(ud_parse.sentences):
                for word in sent.words:
                    synset = None
                    concept = Label.get_or_none(text=word.lemma, language=self.lang)
                    if concept is not None:
                        concept = concept.concepts
                        if word.pos in self.concept_pos:
                            concept = [c for c in concept if
                                       len(re.findall(f"{self.concept_pos[word.pos]}[/$]*", c.sense_label)) > 0]
                    if word.pos in self.pos:
                        synset = wn.synsets(word.lemma, pos=self.pos[word.pos])
                        if len(synset) > 1:
                            # TODO: how to find the best???
                            ss = simple_lesk(sent.text, word.text, pos=self.lesk_pos[word.pos])
                            #sso = original_lesk(self.text, word.text)
                            #ssa = adapted_lesk(self.text, word.text, pos='a')
                            #ssc = cosine_lesk(self.text, word.text, pos='a')
                            synset = ss
                        elif len(synset) == 1:
                            synset = synset[0]
                        else:
                            synset = None
                    self.G.add_node(100*(sent_id+1)+word.id, name=KnowledgeNode(word.text, word.lemma, synset, concept))
                for dep in sent.dependencies:
                    if dep[0].id != 0:
                        self.G.add_edge(100*(sent_id+1)+dep[0].id, 100*(sent_id+1)+dep[2].id, color=dep[1])

    def connect_sentence_graphs(self):
        for node, node_data in self.G.nodes(data=True):
            for other_node, other_node_data in self.G.nodes(data=True):
                if int(node/100) != int(other_node/100):
                    concept_connections = node_data["name"].concept_connection(other_node_data["name"])
                    if len(concept_connections) > 0:
                        concept_connection = max(concept_connections, key=lambda x: x.etc["weight"])
                        self.G.add_edge(node, other_node, color=concept_connection.relation.name)

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
        conceptnet_relation_names = [v for v in RelationName.__dict__.values()]
        show_graph = self.G.copy()
        lines = [u'digraph finite_state_machine {', '\tdpi=70;']
        node_id = {n: i for (i, n) in enumerate(show_graph.nodes)}
        node_lines = []
        for node, n_data in show_graph.nodes(data=True):
            printname = self.d_clean(str(n_data['name']))
            node_line = u'\t{0} [shape = circle, label = "{1}"];'.format(node_id[node], printname).replace('-', '_')
            node_lines.append(node_line)
        lines += sorted(node_lines)
        edge_lines = []
        for u, v, edata in show_graph.edges(data=True):
            if edata['color'] not in conceptnet_relation_names:
                edge_lines.append(u'\t{0} -> {1} [ label = "{2}", color = "green"];'.format(node_id[u], node_id[v],
                                                                                            edata['color']))
            else:
                edge_lines.append(u'\t{0} -> {1} [ label = "{2}", color = "blue"];'.format(node_id[u], node_id[v],
                                                                                           edata['color']))
        lines += sorted(edge_lines)
        lines.append('}')
        return u'\n'.join(lines)
