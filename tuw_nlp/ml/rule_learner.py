from collections import Counter

import numpy as np
from sklearn.linear_model import LogisticRegression

from tuw_nlp.common.vocabulary import Vocabulary
from tuw_nlp.common.eval import print_cat_stats
from tuw_nlp.ml.utils import get_x_y


class RuleLearner():
    def __init__(self, args):
        self.features = Vocabulary()
        self.train_events = []
        self.valid_events = []
        self.feat_count = {
            True: Counter(), False: Counter(), 'total': Counter()}

    def add_train_event(self, features, label):
        event = set(), label
        for feat_string in features:
            feat = self.features.get_id(feat_string, allow_new=True)
            event[0].add(feat)
            self.feat_count[label][feat] += 1
            self.feat_count['total'][feat] += 1

        self.train_events.append(event)

    def add_valid_event(self, features, label):
        event = set(), label
        for feat_string in features:
            if feat_string in self.features.word_to_id:
                feat = self.features.get_id(feat_string)
                event[0].add(feat)

        self.valid_events.append(event)

    def _cutoff_events(self, events):
        return [(feats & self.kept_feats, label) for feats, label in events]

    def cutoff(self, min_freq):
        self.kept_feats = {
            feat for feat, count in self.feat_count['total'].items()
            if count >= min_freq}

        self.train_events = self._cutoff_events(self.train_events)
        self.valid_events = self._cutoff_events(self.valid_events)

    def logreg_choice(self):
        logreg = LogisticRegression(max_iter=500)
        X, y = get_x_y(self.train_events, self.features)
        logreg.fit(X, y)
        weights = logreg.coef_.reshape(-1)
        return [
            feat for feat in np.argsort(weights)[::-1]
            if feat in self.kept_feats]

    def dumb_choice(self, fp_weight=1, min_freq=1):
        def f_weight(f):
            return (
                self.feat_count[True][f] -
                (fp_weight*self.feat_count[False][f]))

        top_features = sorted(
            (
                feat for feat in self.features.id_to_word.keys()
                if self.feat_count['total'][feat] >= min_freq),
            key=f_weight, reverse=True)

        return top_features

    def get_rule_names(self, rules):
        return [self.features.get_word(i) for i in rules]

    def eval_rules(self, rules):
        matches = self.match(rules, self.valid_events)
        stats = {m_type: len(samples) for m_type, samples in matches.items()}
        print_cat_stats({"True": stats})

    def match(self, rules, events):
        matches = {
            match_type: set() for match_type in ("TP", "FP", "TN", "FN")}
        for i, (feats, label) in enumerate(events):
            # if feats.issubset(rules):
            if feats.intersection(rules):
                if label:
                    matches['TP'].add(i)
                else:
                    matches['FP'].add(i)
            else:
                if label:
                    matches['FN'].add(i)
                else:
                    matches['TN'].add(i)
        return matches
