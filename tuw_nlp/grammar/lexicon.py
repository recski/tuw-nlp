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
            ("PROPN", "ADVMOD", "ADJ"),
            ("PROPN", "ADVMOD", "ADV"),
            ("NOUN", "ADVMOD", "ADV"),
            ("NOUN", "ADVMOD", "NUM"),
            ("NOUN", "ADVMOD", "PRON"),
            ("NUM", "ADVMOD", "ADV"),
            ("VERB", "ADVMOD", "ADJ"),
            ("VERB", "ADVMOD", "ADV"),
            ("VERB", "ADVMOD", "PART"),
            ("NOUN", "ADVMOD", "PART"),
            ("PRON", "ADVMOD", "PART"),

            ("ADJ", "OBL_NPMOD", "NOUN"),
            ("ADV", "OBL_NPMOD", "NOUN"),
            ("VERB", "OBL_NPMOD", "NOUN"),

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
            # Up to 85% of viruses that cause respiratory illness are identified by the technology.
            ("SYM", "NUMMOD", "NUM"),

            ("VERB", "ADVCL", "VERB"),
            ("ADJ", "ADVCL", "VERB"),
            ("VERB", "ADVCL", "ADJ"),
            ("VERB", "ADVCL", "NOUN"),
            # The second memorable shift was in September, when the plant made the 75-millionth ton of steel.
            ("PROPN", "ADVCL", "VERB"),
            # Although big city marathons offer great crowd support and a large camaraderie of runners, running in a big city marathon is not for everyone.
            ("PRON", "ADVCL", "VERB"),
            # As the earth revolves around the sun, the place where light shines the brightest changes.
            ("NOUN", "ADVCL", "VERB"),
            # We placed some wax into the old tin can.
            ("VERB", "ADVCL", "AUX"),
            # I have no idea why this rather loud blazer from the GAP was in a bin at my local Dollar Tree.
            ("VERB", "ADVCL", "PROPN"),
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
        obl_tmod = f'f_relation(f_dep1(merge(merge(?2,"(at<relation> / AT :2 (r<root>) :1 (d1<dep1>)))"), r_dep1(?1))))'
        csubj = f'f_dep1(merge(merge(?1,"(r<root> :1 (d1<dep1>))"), r_dep1(?2)))'

        self.bin_fnc = {
            ("ADJ", "NSUBJ", "NOUN"): [r('1')],
            ("VERB", "NSUBJ_PASS", "NOUN"): [r("2")],
            ("VERB", "NSUBJ_PASS", "PRON"): [r("2")],
            ("VERB", "NSUBJ_PASS", "PROPN"): [r("2")],
            # 38% of the world's generated electrical energy is gained from coal.
            ("VERB", "NSUBJ_PASS", "SYM"): [r("2")],

            # CCOMP
            ("VERB", "CCOMP", "VERB"): [r("0")],
            ("VERB", "CCOMP", "ADJ"): [r("2")],
            ("VERB", "CCOMP", "ADJ"): [r("2")],
            # make sure they have a copy of the invoice - sure ->CCOMP -> have
            ("ADJ", "CCOMP", "VERB"): [r("2")],
            ("VERB", "CCOMP", "NOUN"): [r("2")],
            # It is no accident that the title of the exhibition is a homage to one of the classic figures of contemporaneity, Antoni Tapies, whose work breached all the boundaries imposed on artistic creation by the critics.
            ("NOUN", "CCOMP", "NOUN"): [r("2")],

            # OBL
            ("VERB", "OBL", "NOUN"): [r("2")],
            # Show 1 in the series is a documentary detailing the first stages of the celebrity students' conductor training as they enter into a week long 'Baton Camp'.
            ("VERB", "OBL", "PROPN"): [r("2")],
            # Typically, the maximum heat generated from 24 fuel assemblies stored in a cask is less than that given off by a typical home heating system in an hour.
            ("ADJ", "OBL", "PRON"): [r("2")],
            # Up to 85% of viruses that cause respiratory illness are identified by the technology.
            ("VERB", "OBL", "SYM"): [r("2")],
            # The film makes the point that decision-making is an important aspect of such an affair of the heart.
            ("VERB", "OBL_TMOD", "NOUN"): [obl_tmod],

            # ACL
            # An Afghan handed over innocent people into torture. Afghan ADJ?
            ("PROPN", "ACL", "VERB"): [r("0")],
            ("ADJ", "ACL", "VERB"): [r("0")],

            ("NOUN", "ACL", "VERB"): [r("0")],
            ("PROPN", "ACL", "VERB"): [r("0")],
            # The painting was one of the first used as a poster in an advertising campaign for soap powder.
            ("NUM", "ACL", "VERB"): [r("0")],
            # The book asserts the notion that men and women are as different as beings from other planets.
            ("NOUN", "ACL", "ADJ"): [r("0")],
            # It was a dispute discussing the question whether the language of the Greek people (Dimotiki) or a cultivated imitation of Ancient Greek (Katharevousa) should be the official language of the Greek nation.
            ("NOUN", "ACL", "NOUN"): [r("0")],

            # FLAT - Andrew -flat> Wakefield
            ("PROPN", "FLAT", "PROPN"): [r("0")],

            # Parataxis
            ("VERB", "PARATAXIS", "VERB"): [r("0")],
            ("NOUN", "PARATAXIS", "VERB"): [r("0")],
            # 77793 civilians have arrived into the government controlled areas within the last two days.
            ("NUM", "PARATAXIS", "VERB"): [r("0")],
            ("PROPN", "PARATAXIS", "NOUN"): [r("0")],
            # A hairdresser fine-tunes your hair color without causing excessive damage by using toners.
            ("ADJ", "PARATAXIS", "VERB"): [r("0")],
            # The film makes the point that decision-making is an important aspect of such an affair of the heart.
            ("VERB", "PARATAXIS", "NOUN"): [r("0")],
            # The 50g is hands-down, the absolute best calculator for engineers, surveyors, and hackers.
            ("NOUN", "PARATAXIS", "NOUN"): [r("0")],
            # The image is from the poster 'Selling Counterfeit Products is Illegal'.
            ("NOUN", "PARATAXIS", "PROPN"): [r("0")],

            # ACL_RELCL
            ("NOUN", "ACL_RELCL", "VERB"): [r("0")],
            ("PRON", "ACL_RELCL", "VERB"): [r("0")],
            ("NOUN", "ACL_RELCL", "ADJ"): [r("0")],
            ("PROPN", "ACL_RELCL", "VERB"): [r("0")],
            ("NOUN", "ACL_RELCL", "NOUN"): [r("0")],
            ("PROPN", "ACL_RELCL", "NOUN"): [r("0")],

            # NSUBJ
            ("VERB", "NSUBJ", "NOUN"): [r("1")],
            ("VERB", "NSUBJ", "ADJ"): [r("1")],
            ("VERB", "NSUBJ", "PROPN"): [r("1")],
            # One of the guards at the entrance of the supermarket said it had been the same scenario on Saturday with a long queue for sugar being the order of the day.
            ("VERB", "NSUBJ", "NUM"): [r("1")],
            ("VERB", "NSUBJ", "PRON"): [r("1")],
            ("ADJ", "NSUBJ", "PRON"): [r("1")],
            # Ironically, the damage caused by the floods, and the subsequent insurance payout, were what prompted the restoration of the station building.
            ("PRON", "NSUBJ", "NOUN"): [r("1")],
            ("NOUN", "NSUBJ", "PRON"): [r("1")],
            ("NOUN", "NSUBJ", "PROPN"): [r("1")],
            ("ADJ", "NSUBJ", "NOUN"): [r("1")],
            # Jennifer Holt, a former actress from Western movies, was "Aunt Judy," the only human in the cast. human ADJ?
            ("ADJ", "NSUBJ", "PROPN"): [r("1")],
            ("NOUN", "NSUBJ", "NOUN"): [r("1")],
            ("PROPN", "NSUBJ", "NOUN"): [r("1")],
            ("PROPN", "NSUBJ", "PRON"): [r("1")],
            ("ADV", "NSUBJ", "NOUN"): [r("1")],
            # Here is Jose Mojica Marins, the popular Coffin Joe, a filmmaker who invented a cinema of total grossness.
            ("ADV", "NSUBJ", "PROPN"): [r("1")],
            ("ADV", "NSUBJ", "NUM"): [r("1")],
            ("VERB", "NSUBJ", "DET"): [r("1")],
            # Patient survival one year after transplantation from a living-related donor is 95% and comparably high if the organ comes from a cadaveric donor. - For some reason % is the root
            ("SYM", "NSUBJ", "NOUN"): [r("1")],

            # The painting was one of the first used as a poster in an advertising campaign for soap powder.
            ("NUM", "NSUBJ", "NOUN"): [r("1")],
            ("NUM", "NSUBJ", "PROPN"): [r("1")],

            # CSUBJ
            ("ADJ", "CSUBJ", "VERB"): [csubj],
            ("NOUN", "CSUBJ", "VERB"): [csubj],
            ("VERB", "CSUBJ", "VERB"): [csubj],
            ("PROPN", "CSUBJ", "VERB"): [csubj],
            # Although big city marathons offer great crowd support and a large camaraderie of runners, running in a big city marathon is not for everyone.
            ("PRON", "CSUBJ", "VERB"): [csubj],


            ("VERB", "CONJ", "VERB"): [coord],
            ("NOUN", "CASE", "ADP"): [r("0")],

            ("VERB", "XCOMP", "VERB"): [r("2")],
            # make sure they have a copy of the invoice
            ("VERB", "XCOMP", "ADJ"): [r("2")],
            # It becomes a lunch-time respite from the busy city life as a diner relaxes with his buffet delight while watching the commuters waiting alongside each other.
            ("VERB", "XCOMP", "NOUN"): [r("2")],
            ("ADJ", "XCOMP", "VERB"): [r("2")],
            # It's called Symform - a stealthy Seattle outfit founded by a pair of ex-Microsoft employees, Praerit Garg and Bassam Tabbara.
            ("VERB", "XCOMP", "PROPN"): [r("2")],

            # poss
            ("NOUN", "NMOD_POSS", "PRON"): [poss],
            ("NOUN", "NMOD_POSS", "PROPN"): [poss],
            ("NOUN", "NMOD_POSS", "NOUN"): [poss],
            ("PROPN", "NMOD_POSS", "PROPN"): [poss],
            ("PROPN", "NMOD_POSS", "PRON"): [poss],

            # compound
            ("NOUN", "COMPOUND", "NOUN"): [r("0")],
            ("PROPN", "COMPOUND", "PROPN"): [r("0")],
            ("NOUN", "COMPOUND", "PROPN"): [r("0")],
            ("NUM", "COMPOUND", "NUM"): [r("0")],
            # 77793 civilians have arrived into the government controlled areas within the last two days.
            ("VERB", "COMPOUND", "NOUN"): [r("0")],
            ("AUX", "COMPOUND", "NOUN"): [r("0")],

            # obj
            ("VERB", "OBJ", "NOUN"): [r("2")],
            ("VERB", "OBJ", "PRON"): [r("2")],
            ("VERB", "OBJ", "PROPN"): [r("2")],
            # Show 1 in the series is a documentary detailing the first stages of the celebrity students' conductor training as they enter into a week long 'Baton Camp'.
            ("VERB", "OBJ", "NUM"): [r("2")],
            # The company builds many of the machines used in the manufacturing of the beds and the upfitting of the chassis.
            ("VERB", "OBJ", "ADJ"): [r("2")],
            # Local fisherman heated some of their catch cooked over coals in a scuttle.
            ("VERB", "OBJ", "DET"): [r("2")],
            # The company has made available its collection of luxurious full black parts.
            ("ADJ", "OBJ", "NOUN"): [r("2")],

            # appos
            ("NOUN", "APPOS", "PROPN"): [r("0")],
            ("PROPN", "APPOS", "PROPN"): [r("0")],
            # Dalindyebo R900-million and the tribe a further R80-billion in compensation for the humiliation caused by the monarch's criminal trial.
            ("PROPN", "APPOS", "NUM"): [r("0")],
            # Jennifer Holt, a former actress from Western movies, was "Aunt Judy," the only human in the cast.
            ("PROPN", "APPOS", "ADJ"): [r("0")],
            ("NOUN", "APPOS", "NOUN"): [r("0")],
            ("PROPN", "APPOS", "NOUN"): [r("0")],
            ("VERB", "APPOS", "NOUN"): [r("0")],
            # Non-UK students benefit from the bursary scheme.
            ("NOUN", "APPOS", "VERB"): [r("0")],
        }

        self.bin_fnc.update({edge: [r("0")] for edge in self.mod_edges})

        # coordination
        self.bin_fnc.update(
            {("VERB", "CONJ", pos): [coord] for pos in self.npos})

        self.bin_fnc.update(
            {(pos, "CONJ", "VERB"): [coord] for pos in self.npos})

        # I am a semi-professional myself and I also have a small hug of teddy bears, but the photos that Marc Hoberman made of these bears are really fantastic.
        self.bin_fnc.update(
            {("PRON", "CONJ", "VERB"): [coord]})

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
            ],
            "no": [
                n('NEG')
            ],
            "non": [
                n('NEG')
            ]
        }

    def handle_obl_case_mark(self, parent_dep, parent_pos, current_pos, children_pos, i, j, clemma):
        if clemma == "by":
            obl_case = (
                f"{parent_pos} -> HANDLE_{parent_dep}_CASE_{children_pos}_{i}_{j}({children_pos}, {current_pos}, {parent_pos})",
                {'ud': f'{parent_pos}_2(_{parent_dep}_1({current_pos}_2(_CASE_1(?1), ?2)),?3)',
                 'fl': f'f_dep1(merge(merge(?3,"(r<root> :1 (d1<dep1> :0 (r<root>)))"), r_dep1(?2)))'},
                "nonterminal"
            )
        else:
            obl_case = (
                f"{parent_pos} -> HANDLE_{parent_dep}_CASE_{children_pos}_{i}_{j}({children_pos}, {current_pos}, {parent_pos})",
                {'ud': f'{parent_pos}_2(_{parent_dep}_1({current_pos}_2(_CASE_1(?1), ?2)),?3)',
                 'fl': f'f_dep2(f_dep1(merge(merge(merge(?3,"(d1<dep1> :1 (r<root>) :2 (d2<dep2>))"), r_dep1(?1)), r_dep2(?2))))'},
                "nonterminal"
            )

        # The opposition leader has gone into hiding.
        obl_mark = (
            f"{parent_pos} -> HANDLE_{parent_dep}_MARK_{children_pos}_{i}_{j}({children_pos}, {current_pos}, {parent_pos})",
            {'ud': f'{parent_pos}_2(_{parent_dep}_1({current_pos}_2(_MARK_1(?1), ?2)),?3)',
                'fl': f'f_dep2(f_dep1(merge(merge(merge(?3,"(d1<dep1> :1 (r<root>) :2 (d2<dep2>))"), r_dep1(?1)), r_dep2(?2))))'},
            "nonterminal"
        )

        return [obl_case, obl_mark]

    def handle_advcl_mark(self, parent_dep, parent_pos, current_pos, children_pos, i, j, clemma):
        advcl_mark = (
            f"{parent_pos} -> HANDLE_{parent_dep}_MARK_{children_pos}_{i}_{j}({children_pos}, {current_pos}, {parent_pos})",
            {'ud': f'{parent_pos}_2(_{parent_dep}_1({current_pos}_2(_MARK_1(?1), ?2)),?3)',
                'fl': f'f_dep2(f_dep1(merge(merge(merge(?3,"(d1<dep1> :1 (r<root>) :2 (d2<dep2>))"), r_dep1(?1)), r_dep2(?2))))'},
            "nonterminal"
        )

        return [advcl_mark]

    def handle_acl_relcl(self, dep, parent_pos, current_pos, children_pos, i, j):
        acl_relcl = (
            f"{parent_pos} -> HANDLE_ACL_RELCL_NSUBJ_{children_pos}_{i}_{j}({children_pos}, {current_pos}, {parent_pos})",
            {'ud': f'{parent_pos}_2(_ACL_RELCL_1({current_pos}_2(_NSUBJ_1(?1), ?2)),?3)',
             'fl': f'f_dep1(merge(merge(?3,"(r<root> :0 (d1<dep1> :1 (r<root>)))"), r_dep1(?2)))'},
            "nonterminal"
        )

        acl_relcl2 = (
            f"{parent_pos} -> HANDLE_ACL_RELCL_NSUBJ_PASS_{children_pos}_{i}_{j}({children_pos}, {current_pos}, {parent_pos})",
            {'ud': f'{parent_pos}_2(_ACL_RELCL_1({current_pos}_2(_NSUBJ_PASS_1(?1), ?2)),?3)',
             'fl': f'f_dep1(merge(merge(?3,"(r<root> :0 (d1<dep1> :1 (r<root>)))"), r_dep1(?2)))'},
            "nonterminal"
        )
        return [acl_relcl, acl_relcl2]

    def handle_subgraphs(self, lemma, pos, clemma, cpos, dep, parent, i, j):
        parent_dep = parent[2]
        parent_pos = parent[1]

        if parent_dep in ("NMOD", "OBL", "OBL_NPMOD"):
            return self.handle_obl_case_mark(
                parent_dep, parent_pos, pos, cpos, i, j, clemma)
        if parent_dep in ("ADVCL"):
            return self.handle_advcl_mark(
                parent_dep, parent_pos, pos, cpos, i, j, clemma)
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
            # Aussenminister ... der strunzdumm ist
            ("NOUN", "ACL", "ADJ"),
            ("NOUN", "NUMMOD", "NUM"),
            ("NUM", "ADVMOD", "ADV"),
            # maximal 6,0 m
            ("NUM", "ADVMOD", "ADJ"),
            ("NUM", "ADVMOD", "NUM"),
            ("VERB", "ADVMOD", "ADJ"),
            ("VERB", "ADVMOD", "ADV"),
            # nicht staffeln, sample 10
            ("VERB", "ADVMOD", "PART"),
            # sample 112 of sample_10
            ("VERB", "ADVCL", "VERB"),
            # nicht gewaehlt... , weil er gegen die Homo-Ehe... (Germeval '18)
            ("VERB", "ADVCL", "ADJ"),
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
            # Verloren ist die Zeit
            ("NOUN", "NSUBJ", "NOUN"): [r('1')],
            ("PROPN", "NSUBJ", "NOUN"): [r('1')],
            ("NOUN", "NSUBJ", "PROPN"): [r('1')],
            ("VERB", "NSUBJ_PASS", "NOUN"): [r("2")],
            # jeder der ... paktiert, hat ... verschissen
            ("VERB", "CSUBJ", "VERB"): [r("1")],
            # ...wird bestimmt, dass...
            ("VERB", "CSUBJ_PASS", "VERB"): [r("2")],
            # ...wird bestimmt, dass...
            ("VERB", "CCOMP", "VERB"): [r("2")],
            # ...wird bestimmt: Die Errichtung...zulaesssig (8159_21_0)
            # ...wird bestimmt: ...betragen
            # parsed as parataxis
            ("VERB", "PARATAXIS", "ADJ"): [r("2")],
            ("VERB", "PARATAXIS", "VERB"): [r("2")],
            # ...so auszubilden, dass...
            ("VERB", "CCOMP", "ADJ"): [r("0")],  # TODO
            # sind Vorkehrungen zu treffen, dass...moeglich
            ("NOUN", "CCOMP", "ADJ"): [r("0")],  # TODO
            # sind Vorkehrungen zu treffen, dass...bleiben
            ("NOUN", "CCOMP", "VERB"): [r("0")],  # TODO
            # vorhanden bleiben (correct parse? why not obj or obl?)
            ("VERB", "XCOMP", "ADJ"): [r("2")],  # TODO
            # hat ... zu tun (Germeval '18)
            ("VERB", "XCOMP", "VERB"): [r("2")],  # TODO
            ("VERB", "OBJ", "NOUN"): [r("2")],
            # habt ihr Angst
            ("AUX", "OBJ", "NOUN"): [r("2")],
            ("NOUN", "OBJ", "NOUN"): [r("2")],
            ("VERB", "OBJ", "PROPN"): [r("2")],
            # hat nichts... (Germeval '18)
            ("VERB", "OBJ", "PRON"): [r("2")],
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
            ("VERB", "NSUBJ", "PROPN"): [r("1")],
            ("VERB", "CONJ", "VERB"): [coord],
            ("VERB", "CONJ", "AUX"): [coord],
            ("NOUN", "CASE", "ADP"): [r("0")],
            # 7181_3_1
            ("NOUN", "APPOS", "PROPN"): [r("0")],
            ("PROPN", "APPOS", "PROPN"): [r("0")],
            ("PROPN", "FLAT", "PROPN"): [r("0")],
            ("NOUN", "COMPOUND", "NOUN"): [r("0")],
            # Rede ... jetzt
            ("NOUN", "APPOS", "ADV"): [r("0")]
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
