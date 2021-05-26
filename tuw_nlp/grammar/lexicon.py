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
        return NotImplementedError

    def get_dependency_rules(self, pos, dep, cpos):
        """this is kept even simpler: all three have to be listed for every
        lexicon entry.
        TODO: allow lookup based on lemma and/or clemma (that's 3 options)"""
        return self.bin_fnc.get((pos, dep, cpos)) or [self.default_binary_rule]

    def get_terminal_rules(self, word, pos, **kwargs):
        raise NotImplementedError

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


class BaseLexicon(IRTGRuleLexicon):
    def __init__(self):
        super(BaseLexicon, self).__init__()

        # if a dependency is not handled, the dependent is ignored
        self.default_binary_rule = "?2"

    def get_binary_fnc(self):
        raise NotImplementedError

    def get_term_fnc(self):
        raise NotImplementedError

    def get_terminal_rules(self, word, pos, xpos):
        """returns a list of interpretations associated with the
        word or word, pos pair. Word-only match takes precedence to discourage
        using it as an elsewhere condition: if POS matters then
        the word should be listed with all possible POS-tags"""

        if xpos == 'VVIZU':
            return [f'"({word}<root> / {word} :0 (OBL / OBL))"']

        return self.term_fnc.get(word, self.term_fnc.get(
            (word, pos))) or [self.get_default_terminal(word)]

    def get_lexical_terminal(self, word):
        return self.get_default_terminal(word)

    def get_default_terminal(self, word):
        return f'"({word}<root> / {word})"'


class ENLexicon(BaseLexicon):
    def __init__(self):
        super(ENLexicon, self).__init__()

    def get_mod_edges(self):
        self.mod_edges = {
            ("ADJ", "ADVMOD", "ADV"),
            ("ADJ", "ADVMOD", "PART"),
            ("ADJ", "ADVMOD", "ADJ"),
            ("NOUN", "ADVMOD", "ADV"),
            ("NOUN", "ADVMOD", "NUM"),
            ("NOUN", "ADVMOD", "PRON"),
            ("NUM", "ADVMOD", "ADV"),
            ("VERB", "ADVMOD", "ADJ"),
            ("VERB", "ADVMOD", "ADV"),
            ("VERB", "ADVMOD", "PART"),
            ("NOUN", "ADVMOD", "PART"),

            ("NOUN", "NMOD", "NOUN"),
            ("NOUN", "NMOD", "PROPN"),
            ("PROPN", "NMOD", "PROPN"),
            ("NOUN", "NMOD", "PRON"),

            ("NOUN", "AMOD", "ADJ"),
            ("NOUN", "AMOD", "VERB"),
            ("PROPN", "AMOD", "ADJ"),
            ("PRON", "AMOD", "ADJ"),

            ("NOUN", "ACL", "VERB"),

            ("NOUN", "NUMMOD", "NUM"),

            ("VERB", "ADVCL", "VERB"),
            ("ADJ", "ADVCL", "VERB"),
        }

        self.mod_edges |= {
            (pos1, dep, pos2)
            for pos1 in self.npos for pos2 in self.npos for dep in (
                "NMOD", "AMOD")}

    def get_binary_fnc(self):
        def r(edge):
            return f'f_dep1(merge(merge(?2,"(r<root> :{edge} (d1<dep1>))"), r_dep1(?1)))'  # noqa

        coord = f'f_dep1(f_dep2(merge(merge(r_dep1(?1),"(coord<root> / COORD :0 (d1<dep1>) :0 (d2<dep2>))"), r_dep2(?2))))'  # noqa
        poss = f'f_relation(f_dep1(merge(merge(?2,"(has<relation> / HAS :2 (r<root>) :1 (d1<dep1>)))"), r_dep1(?1))))'

        self.bin_fnc = {
            ("ADJ", "NSUBJ", "NOUN"): [r('1')],
            ("VERB", "NSUBJ_PASS", "NOUN"): [r("2")],
            ("VERB", "NSUBJ_PASS", "PRON"): [r("2")],
            ("VERB", "NSUBJ_PASS", "PROPN"): [r("2")],
            ("VERB", "CCOMP", "VERB"): [r("2")],
            ("VERB", "CCOMP", "ADJ"): [r("2")],
            # make sure they have a copy of the invoice - sure ->CCOMP -> have
            ("ADJ", "CCOMP", "VERB"): [r("2")],

            ("VERB", "OBL", "NOUN"): [r("2")],

            # NSUBJ
            ("VERB", "NSUBJ", "NOUN"): [r("1")],
            ("VERB", "NSUBJ", "ADJ"): [r("1")],
            ("VERB", "NSUBJ", "PROPN"): [r("1")],

            # CSUBJ
            ("ADJ", "CSUBJ", "VERB"): [r("1")],
            ("NOUN", "CSUBJ", "VERB"): [r("1")],
            ("VERB", "CSUBJ", "VERB"): [r("1")],


            ("VERB", "CONJ", "VERB"): [coord],
            ("NOUN", "CASE", "ADP"): [r("0")],

            ("VERB", "XCOMP", "VERB"): [r("2")],
            # make sure they have a copy of the invoice
            ("VERB", "XCOMP", "ADJ"): [r("2")],
            ("ADJ", "XCOMP", "VERB"): [r("2")],

            # poss
            ("NOUN", "NMOD_POSS", "PRON"): [poss],
            ("NOUN", "NMOD_POSS", "PROPN"): [poss],
            ("NOUN", "NMOD_POSS", "NOUN"): [poss],
            ("PROPN", "NMOD_POSS", "PROPN"): [poss],
            ("PROPN", "NMOD_POSS", "PRON"): [poss],

            # obj
            ("VERB", "OBJ", "NOUN"): [r("2")],
            ("VERB", "OBJ", "PRON"): [r("2")],
            ("VERB", "OBJ", "PROPN"): [r("2")],
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
            "not": [
                n('NEG')
            ],
            "none": [
                n('NEG')
            ]
        }

    def handle_obl_case(self, parent_dep, parent_pos, current_pos, children_pos, i, clemma):
        if clemma == "by":
            obl_case = (
                f"{parent_pos} -> HANDLE_{parent_dep}_CASE_{children_pos}_{i}({children_pos}, {current_pos}, {parent_pos})",
                {'ud': f'{parent_pos}_2(_{parent_dep}_1({current_pos}_2(_CASE_1(?1), ?2)),?3)',
                 'fl': f'f_dep1(merge(merge(?3,"(r<root> :1 (d1<dep1> :0 (r<root>)))"), r_dep1(?2)))'},
                "nonterminal"
            )
        else:
            obl_case = (
                f"{parent_pos} -> HANDLE_{parent_dep}_CASE_{children_pos}_{i}({children_pos}, {current_pos}, {parent_pos})",
                {'ud': f'{parent_pos}_2(_{parent_dep}_1({current_pos}_2(_CASE_1(?1), ?2)),?3)',
                 'fl': f'f_dep2(f_dep1(merge(merge(merge(?3,"(d1<dep1> :1 (r<root>) :2 (d2<dep2>))"), r_dep1(?1)), r_dep2(?2))))'},
                "nonterminal"
            )

        return [obl_case]

    def handle_acl_relcl(self, dep, parent_pos, current_pos, children_pos, i, j):
        acl_relcl = (
            f"{parent_pos} -> HANDLE_ACL_RELCL_NSUBJ_{children_pos}_{i}_{j}({children_pos}, {current_pos}, {parent_pos})",
            {'ud': f'{parent_pos}_2(_ACL_RELCL_1({current_pos}_2(_NSUBJ_1(?1), ?2)),?3)',
             'fl': f'f_dep1(merge(merge(?3,"(r<root> :1 (d1<dep1> :0 (r<root>)))"), r_dep1(?2)))'},
            "nonterminal"
        )

        acl_relcl2 = (
            f"{parent_pos} -> HANDLE_ACL_RELCL_NSUBJ_PASS_{children_pos}_{i}_{j}({children_pos}, {current_pos}, {parent_pos})",
            {'ud': f'{parent_pos}_2(_ACL_RELCL_1({current_pos}_2(_NSUBJ_PASS_1(?1), ?2)),?3)',
             'fl': f'f_dep1(merge(merge(?3,"(r<root> :1 (d1<dep1> :0 (r<root>)))"), r_dep1(?2)))'},
            "nonterminal"
        )
        return [acl_relcl, acl_relcl2]

    def handle_subgraphs(self, lemma, pos, clemma, cpos, dep, parent, i, j):
        parent_dep = parent[2]
        parent_pos = parent[1]

        if parent_dep in ("NMOD", "OBL"):
            return self.handle_obl_case(
                parent_dep, parent_pos, pos, cpos, i, clemma)
        if parent_dep == "ACL_RELCL":
            return self.handle_acl_relcl(dep, parent_pos, pos, cpos, i, j)

        return


class CFLLexicon(BaseLexicon):
    def __init__(self):
        super(CFLLexicon, self).__init__()

    def get_mod_edges(self):
        self.mod_edges = {
            ("ADJ", "ADVMOD", "ADV"),
            # nicht hoeher, 7774_18_1
            ("ADJ", "ADVMOD", "PART"),
            # tatsaechlich errichteten, 7774_18_1
            ("ADJ", "ADVMOD", "ADJ"),
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
            # ("VERB", "OBL", "NOUN"),
        }

        self.mod_edges |= {
            (pos1, dep, pos2)
            for pos1 in self.npos for pos2 in self.npos for dep in (
                "NMOD", "AMOD")}

    def get_binary_fnc(self):
        def r(edge):
            return f'f_dep1(merge(merge(?2,"(r<root> :{edge} (d1<dep1>))"), r_dep1(?1)))'  # noqa

        coord = f'f_dep1(f_dep2(merge(merge(r_dep1(?1),"(coord<root> / COORD :0 (d1<dep1>) :0 (d2<dep2>))"), r_dep2(?2))))'  # noqa

        self.bin_fnc = {
            # Errichtung ist untersagt
            ("ADJ", "NSUBJ", "NOUN"): [r('1')],
            ("VERB", "NSUBJ_PASS", "NOUN"): [r("2")],
            # ...wird bestimmt, dass...
            ("VERB", "CSUBJ_PASS", "VERB"): [r("2")],
            # ...wird bestimmt, dass...
            ("VERB", "CCOMP", "VERB"): [r("2")],
            # ...wird bestimmt: Die Errichtung...zulaesssig (8159_21_0)
            # erroneously parsed as parataxis
            ("VERB", "PARATAXIS", "ADJ"): [r("2")],
            # ...so auszubilden, dass...
            ("VERB", "CCOMP", "ADJ"): [r("0")],  # TODO
            # sind Vorkehrungen zu treffen, dass...moeglich
            ("NOUN", "CCOMP", "ADJ"): [r("0")],  # TODO
            # sind Vorkehrungen zu treffen, dass...bleiben
            ("NOUN", "CCOMP", "VERB"): [r("0")],  # TODO
            # vorhanden bleiben (correct parse? why not obj or obl?)
            ("VERB", "XCOMP", "ADJ"): [r("2")],  # TODO
            ("VERB", "OBJ", "NOUN"): [r("2")],
            # Fuer alle Flaechen ... zu treffen # TODO
            ("VERB", "OBL", "NOUN"): [r("2")],
            # zu begruenen, e.g. 7181_6_0
            ("VERB", "MARK", "PART"): [r("0")],
            # sofern.., e.g. 7408_10_1
            ("VERB", "MARK", "SCONJ"): [r("0")],
            ("VERB", "NSUBJ", "NOUN"): [r("1")],
            # ...Pflanzung möglich ist...
            ("VERB", "NSUBJ", "ADJ"): [r("1")],
            ("VERB", "NSUBJ", "PRON"): [r("1")],
            ("VERB", "CONJ", "VERB"): [coord],
            ("NOUN", "CASE", "ADP"): [r("0")],
            # 7181_3_1
            ("NOUN", "APPOS", "PROPN"): [r("0")]
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
            "sofern": [
                n('EXC')
            ],
            "untersagen": [
                n('FOR')
            ],
            "unzulaessig": [
                n('FOR')
            ],
            ("zu", "PART"): [
                n('OBL')
            ],
        }

    def handle_obl_case(self, parent_dep, parent_pos, current_pos, children_pos, i, clemma):
        obl_case = (
            f"{parent_pos} -> HANDLE_{parent_dep}_CASE_{children_pos}_{i}({children_pos}, {current_pos}, {parent_pos})",
            {'ud': f'{parent_pos}_2(_{parent_dep}_1({current_pos}_2(_CASE_1(?1), ?2)),?3)',
             'fl': f'f_dep2(f_dep1(merge(merge(merge(?3,"(d1<dep1> :1 (r<root>) :2 (d2<dep2>))"), r_dep1(?1)), r_dep2(?2))))'},
            "nonterminal"
        )

        return [obl_case]

    def handle_subgraphs(self, lemma, pos, clemma, cpos, dep, parent, i, j):
        parent_dep = parent[2]
        parent_pos = parent[1]

        if parent_dep in ("NMOD", "OBL"):
            return self.handle_obl_case(
                parent_dep, parent_pos, pos, cpos, i, clemma)

        return
