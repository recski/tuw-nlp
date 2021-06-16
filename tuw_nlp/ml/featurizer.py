import logging
import os

import stanza

from tuw_nlp.graph.lexical import LexGraphs
from tuw_nlp.graph.utils import graph_to_pn
from tuw_nlp.grammar.text_to_4lang import TextTo4lang
from tuw_nlp.text.pipeline import CachedStanzaPipeline
from tuw_nlp.text.preprocessor import Preprocessor


class Featurizer():
    def __init__(self, cache_dir='cache', lang=None, preprocessor=None):
        self.feat_names = {}
        self.cache_dir = cache_dir
        self.lang = lang
        self.preproc = Preprocessor(preprocessor)

    def gen_events(self, iterable):
        raise NotImplementedError

    def get_feat_name(self, feat):
        return self.feat_names.get(feat, feat)


class TFLFeaturizer(Featurizer):
    def __init__(self, *args, **kwargs):
        super(TFLFeaturizer, self).__init__(*args, **kwargs)

        self.lexgraphs = LexGraphs()
        self.nlp_cache = os.path.join(self.cache_dir, 'nlp_cache.json')

    def get_features(self, fl, tfl):
        features = set()
        for sg_tuple, sg in self.lexgraphs.gen_lex_subgraphs(fl, 2):
            features.add(sg_tuple)
            self.feat_names[sg_tuple] = graph_to_pn(sg)
        return list(features)

    def gen_events(self, iterable):
        with TextTo4lang(
                lang=self.lang, nlp_cache=self.nlp_cache,
                cache_dir=self.cache_dir) as tfl:

            for raw_text, label in iterable:
                text = self.preproc(raw_text)
                features = []
                try:
                    for fl in tfl(text):
                        features += self.get_features(fl, tfl)
                except TypeError:
                    logging.error(f'tfl error on this text: {text}')

                yield features, label


class SimpleFeaturizer(Featurizer):
    def __init__(self, *args, **kwargs):
        super(SimpleFeaturizer, self).__init__(*args, **kwargs)
        self.nlp_cache = os.path.join(self.cache_dir, 'nlp_cache.json')
        self.nlp_init = lambda: stanza.Pipeline(lang=self.lang)

    def get_features(self, raw_text, nlp):
        text = self.preproc(raw_text)
        doc = nlp(text)
        feats = set()
        for sen in doc.sentences:
            for tok in sen.words:
                # feats.append(f'{tok.lemma}_{tok.xpos}')
                if tok.upos not in ('NOUN', 'PROPN'):
                    feats.add(tok.lemma)
                # feats.add(tok.text)

        return list(feats)

    def gen_events(self, iterable):
        with CachedStanzaPipeline(
                None, self.nlp_cache, init=self.nlp_init) as nlp:
            for raw_text, label in iterable:
                text = self.preproc(raw_text)
                features = self.get_features(text, nlp)
                yield features, label


def get_featurizer(method, cache_dir='cache', lang=None, preprocessor=None):
    if method == 'fl':
        featurizer_cls = TFLFeaturizer
    elif method == 'simple':
        featurizer_cls = SimpleFeaturizer

    return featurizer_cls(
        cache_dir=cache_dir, lang=lang, preprocessor=preprocessor)
