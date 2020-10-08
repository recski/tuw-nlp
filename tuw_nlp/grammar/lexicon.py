import os

from tuw_nlp.text.patterns.misc import CHAR_REPLACEMENTS


class IRTGRuleLexicon():
    def __init__(self):
        self.get_props_from_file('propositions.txt')
        self.npos = ("NOUN", "ADJ", "PROPN", "ADV")
        self.get_mod_edges()
        self.get_term_fnc()
        self.get_binary_fnc()

    def get_mod_edges(self):
        self.mod_edges = {
            ("ADJ", "ADVMOD", "ADV"),
            # zulaessig -> bis, sample 6
            ("ADJ", "CASE", "ADP"),
            # bis -> Ausladung, sample 6
            ("ADP", "NMOD", "NOUN"),
            # Raum darueber, 318 of sample_10
            ("NOUN", "ADVMOD", "ADV"),
            ("NOUN", "ADVMOD", "NUM"),
            # kein Dachgaube, sample 4
            ("NOUN", "ADVMOD", "PRON"),
            # Gebaeudefront_NOUN -AMOD-> bzw_VERB, sample 11
            ("NOUN", "AMOD", "VERB"),
            # Gebaeudefront_NOUN -ACL-> liegen_VERB, sample 5
            ("NOUN", "ACL", "VERB"),
            ("NOUN", "NUMMOD", "NUM"),
            ("NUM", "ADVMOD", "ADV"),
            ("NUM", "ADVMOD", "ADV"),
            ("NUM", "ADVMOD", "NUM"),
            ("VERB", "ADVMOD", "ADJ"),
            ("VERB", "ADVMOD", "ADV"),
            # nicht staffeln, sample 10
            ("VERB", "ADVMOD", "PART"),
            # sample 112 of sample_10
            ("VERB", "ADVCL", "VERB"),
            # betragen duerfen, sample 13
            ("VERB", "AUX", "AUX"),
            # liegen -> Baulinie, sample 6
            ("VERB", "OBL", "NOUN"),
            }

        self.mod_edges |= {
            (pos1, dep, pos2)
            for pos1 in self.npos for pos2 in self.npos for dep in (
                "NMOD", "AMOD")}

    def get_dependency_rules(self, pos, dep, cpos):
        """this is kept even simpler: all three have to be listed for every
        lexicon entry.
        TODO: allow lookup based on lemma and/or clemma (that's 3 options)"""
        return self.bin_fnc.get((pos, dep, cpos)) or [self.default_binary_rule]

    def get_terminal_rules(self, word, pos):
        """returns a list of interpretations associated with the
        word or word, pos pair. Word-only match takes precedence to discourage
        using it as an elsewhere condition: if POS matters then
        the word should be listed with all possible POS-tags"""

        if word in self.prop or (word, pos) in self.prop or word[0] == 'X':
            # return [f"[prop: {word}]"]
            return [self.get_lexical_terminal(word)]

        return self.term_fnc.get(word, self.term_fnc.get(
            (word, pos))) or [self.get_default_terminal(word)]

    def get_props_from_file(self, fn):
        self.prop = set()
        with open(os.path.join(
                os.path.dirname(os.path.abspath(__file__)), fn)) as PF:
            for line in PF:
                w = line.strip()
                for a, b in CHAR_REPLACEMENTS.items():
                    w = w.replace(a, b)
                self.prop.add(w)

    def get_binary_fnc(self):
        raise NotImplementedError

    def get_term_fnc(self):
        raise NotImplementedError

    def get_lexical_terminal(self, word):
        raise NotImplementedError

    def get_default_terminal(self, word):
        raise NotImplementedError


class FSLexicon(IRTGRuleLexicon):
    def __init__(self):
        super(FSLexicon, self).__init__()
        self.default_binary_rule = "unify(?1, ?2)"

    def get_binary_fnc(self):
        self.bin_fnc = {
            # Errichtung ist untersagt
            ("ADJ", "NSUBJ", "NOUN"): ["unify(emb_prop(?1), ?2)"],
            ("VERB", "NSUBJ_PASS", "NOUN"): ["unify(emb_obj(?1), ?2)"],
            ("VERB", "NSUBJ", "NOUN"): ["unify(emb_subj(?1), ?2)"],
            ("VERB", "CONJ", "VERB"): [
                'unify(emb_coord1(?1), emb_coord2(?2))'],
            ("NOUN", "CASE", "ADP"): ["emb_prop(unify(?1, emb_mod(?2)))"]
            }

        self.bin_fnc.update({
            edge: ["emb_prop(unify(emb_mod(?1), ?2))"]
            for edge in self.mod_edges})

        # coordination
        self.bin_fnc.update({
            (pos1, "CONJ", pos2): ['unify(emb_coord1(?1), emb_coord2(?2))']
            for pos1 in self.npos for pos2 in self.npos})

    def get_term_fnc(self):
        self.term_fnc = {
            "nicht": [
                '"[neg: 1]"'
            ],
            "kein": [
                '"[neg: 1]"'
            ],
            "duerfen": [
                '"[per: 1]"'
            ],
            "muessen": [
                '"[obl: 1]"'
            ],
            "zulaessig": [
                '"[per: 1]"'
            ],
            "untersagen": [
                '"[for: 1]"'
            ],
            "unzulaessig": [
                '"[for: 1]"'
            ],
        }

    def get_lexical_terminal(self, word):
        return f'"[prop: {word}]"'

    def get_default_terminal(self, word):
        return '"[]"'


class CFLLexicon(IRTGRuleLexicon):
    def __init__(self):
        super(CFLLexicon, self).__init__()

        # if a dependency is not handled, the dependent is ignored
        self.default_binary_rule = "?2"

    def get_binary_fnc(self):
        def r(edge):
            return f'f_dep1(merge(merge(?2,"(r<root> :{edge} (d1<dep1>))"), r_dep1(?1)))'  # noqa

        coord = f'f_dep1(f_dep2(merge(merge(r_dep1(?1),"(coord<root> / COORD :0 (d1<dep1>) :0 (d2<dep2>))"), r_dep2(?2))))'  # noqa

        self.bin_fnc = {
            # Errichtung ist untersagt
            ("ADJ", "NSUBJ", "NOUN"): [r('1')],
            ("VERB", "NSUBJ_PASS", "NOUN"): [r("2")],
            ("VERB", "OBJ", "NOUN"): [r("2")],
            ("VERB", "NSUBJ", "NOUN"): [r("1")],
            ("VERB", "NSUBJ", "PRON"): [r("1")],
            ("VERB", "CONJ", "VERB"): [coord],
            ("NOUN", "CASE", "ADP"): [r("0")]
            }

        self.bin_fnc.update({edge: [r("0")] for edge in self.mod_edges})

        # coordination
        self.bin_fnc.update(
            {("VERB", "CONJ", pos): [coord] for pos in self.npos})

        self.bin_fnc.update(
            {(pos, "CONJ", "VERB"): [coord] for pos in self.npos})

        self.bin_fnc.update({
            (pos1, "CONJ", pos2): [coord]
            for pos1 in self.npos for pos2 in self.npos})

    def get_term_fnc(self):
        def n(label):
            return self.get_default_terminal(label)

        self.term_fnc = {
            "nicht": [
                n('NEG')
            ],
            "kein": [
                n('NEG')
            ],
            "duerfen": [
                n('PER')
            ],
            "muessen": [
                n('OBL')
            ],
            "zulaessig": [
                n('PER')
            ],
            "untersagen": [
                n('FOR')
            ],
            "unzulaessig": [
                n('FOR')
            ],
        }

    def get_lexical_terminal(self, word):
        return self.get_default_terminal(word)

    def get_default_terminal(self, word):
        return f'"({word}<root> / {word})"'
