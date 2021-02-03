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
            ("VERB", "NSUBJ", "NOUN"): [r("1")],
            # ...Pflanzung möglich ist...
            ("VERB", "NSUBJ", "ADJ"): [r("1")],
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


class DefaultLexicon():
    def __init__(self):
        self.bin_fnc = {}
        self.relation_terms = set()

        def r_out(ud_edge, fourlang_edge):
            return f'f_dep1(merge(merge(?1,"(r<root> :{ud_edge} (d1<dep1>))"), r_dep1(?2)))', f'f_dep1(merge(merge(?1,"(r<root> :{fourlang_edge} (d1<dep1>))"), r_dep1(?2)))'

        def r_in(ud_edge, fourlang_edge):
            return f'f_dep1(merge(merge(?1,"(r<root> :{ud_edge} (d1<dep1>))"), r_dep1(?2)))', f'f_dep1(merge(merge(?1,"(d1<dep1> :{fourlang_edge} (r<root>))"), r_dep1(?2)))'

        def r_relation(ud_edge, relation):
            return f'f_dep1(merge(merge(?1,"(r<root> :{ud_edge} (d1<dep1>))"), r_dep1(?2)))', f'f_dep1(merge(merge(?1,"({relation}<relation> / {relation} :2 (r<root>) :1 (d1<dep1>)))"), r_dep1(?2)))'

        def r_in_out(ud_edge, fourlang_in, fourlang_out):
            return f'f_dep1(merge(merge(?1,"(r<root> :{ud_edge} (d1<dep1>))"), r_dep1(?2)))', f'f_dep1(merge(merge(?1,"(r<root> :{fourlang_out} (d1<dep1> :{fourlang_in} (r<root>)))"), r_dep1(?2)))'

        def r_default_binary_rule(ud_edge):
            return f'f_dep1(merge(merge(?1,"(r<root> :{ud_edge} (d1<dep1>))"), r_dep1(?2)))', f'f_dep1(merge(merge(?1,"(r<root> :UNKNOWN (d1<dep1>))"), r_dep1(?2)))'

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sorted_train_edges_mapped"), "r+") as f:
            for line in f:
                line = line.strip("\n")
                if line:
                    line = line.split("\t")
                    pos = line[0]
                    dep = line[2].replace(":", "_").upper()
                    cpos = line[1]
                    out_edge = None if line[4] == "-" else line[4]
                    in_edge = None if line[5] == "-" else line[5]

                    if in_edge and not out_edge:
                        self.bin_fnc[(pos, dep, cpos)] = r_in(dep, in_edge)
                    elif not in_edge and out_edge:
                        self.bin_fnc[(pos, dep, cpos)] = r_out(dep, out_edge)
                    elif in_edge and out_edge:
                        self.bin_fnc[(pos, dep, cpos)] = r_in_out(
                            dep, in_edge, out_edge)
                    elif not in_edge and not out_edge and len(line) == 7:
                        self.relation_terms.add(line[6])
                        self.bin_fnc[(pos, dep, cpos)] = r_relation(
                            dep, line[6])
                    else:
                        self.bin_fnc[(pos, dep, cpos)
                                     ] = r_default_binary_rule(dep)

    def get_dependency_rules(self, pos, dep, cpos):
        rule = self.bin_fnc.get((pos, dep, cpos)) or self.get_default_binary_rule(dep)
        return [rule]

    def get_default_terminal(self, word, i):
        return f'"({word}_{i}<root> / {word})"', f'"({word}<root> / {word})"'

    def get_relation_terminal(self, word):
        return f'"({word}<relation> / {word})"', f'"({word}<relation> / {word})"'

    def handle_conj(self, parent_pos, parent_dep, current_pos, children_pos, i):
        coordination = (
            f"{parent_pos} -> coordination_{i}(SUBGRAPHNODE, COORD)",
            {'ud': f'f_dep1(merge(merge(?1,"(r<root> :{parent_dep} (d1<dep1>))"), r_dep1(?2)))',
             'fourlang': f'r_coord_root(merge(?1, ?2))'},
            "nonterminal"
        )

        handle_coord = (
            f"COORD -> handle_coord_{i}(COORD, {children_pos})",
            {
                'ud': f'f_dep1(merge(merge(?1,"(r<root> :CONJ (d1<dep1>))"), r_dep1(?2)))',
                'fourlang': f'f_dep1(merge(merge(?1,"(r<coord> :2 (d1<dep1>))"), r_dep1(?2)))'},
            "nonterminal"
        )

        coord_to_pos = (
            f"COORD -> coord_to_{current_pos}{i}({current_pos})",
            {'ud': f'?1',
             'fourlang': f'f_dep1(merge("(r<coord> :2 (d1<dep1>))", r_dep1(?1)))'},
            "nonterminal"
        )

        subgraph_node = (
            f"SUBGRAPHNODE -> subgraph_to_node{i}({parent_pos})",
            {'ud': f'?1',
             'fourlang': f'r_coord(?1)'},
            "nonterminal"
        )

        return [coordination, handle_coord, coord_to_pos, subgraph_node]

    def handle_acl_relcl(self, parent_pos, current_pos, children_pos, i, j):
        acl_relcl = (
            f"{parent_pos} -> handle_acl_relcl{i}_{j}({parent_pos}, {current_pos}, {children_pos})",
            {'ud': f'f_dep2(merge(merge(?1,"(r<root> :ACL_RELCL (d2<dep2>))"), r_dep2(f_dep1(merge(merge(?2,"(r<root> :NSUBJ (d1<dep1>))"), r_dep1(?3))))))',
             'fourlang': f'f_dep1(merge(merge(?1,"(r<root> :0 (d1<dep1>))"), r_dep1(?2)))'},
            "nonterminal"
        )

        acl_relcl2 = (
            f"{parent_pos} -> handle_acl_relcl{i}_{j}_pass({parent_pos}, {current_pos}, {children_pos})",
            {'ud': f'f_dep2(merge(merge(?1,"(r<root> :ACL_RELCL (d2<dep2>))"), r_dep2(f_dep1(merge(merge(?2,"(r<root> :NSUBJ_PASS (d1<dep1>))"), r_dep1(?3))))))',
             'fourlang': f'f_dep1(merge(merge(?1,"(r<root> :0 (d1<dep1>))"), r_dep1(?2)))'},
            "nonterminal"
        )
        return [acl_relcl, acl_relcl2]

    def handle_obl_case(self, parent_pos, current_pos, children_pos, i, clemma):
        if clemma == "by":
            obl_case = (
                f"{parent_pos} -> handle_obl_case{i}({parent_pos}, {current_pos}, {children_pos})",
                {'ud': f'f_dep2(merge(merge(?1,"(r<root> :OBL (d2<dep2>))"), r_dep2(f_dep1(merge(merge(?2,"(r<root> :CASE (d1<dep1>))"), r_dep1(?3))))))',
                'fourlang': f'f_dep1(merge(merge(?1,"(r<root> :1 (d1<dep1> :0 (r<root>)))"), r_dep1(?2)))'},
                "nonterminal"
            )
        else:
            obl_case = (
                f"{parent_pos} -> handle_obl_case{i}({parent_pos}, {current_pos}, {children_pos})",
                {'ud': f'f_dep2(merge(merge(?1,"(r<root> :OBL (d2<dep2>))"), r_dep2(f_dep1(merge(merge(?2,"(r<root> :CASE (d1<dep1>))"), r_dep1(?3))))))',
                'fourlang': f'f_dep2(f_dep1(merge(merge(merge(?1,"(d1<dep1> :1 (r<root>) :2 (d2<dep2>))"), r_dep1(?3)), r_dep2(?2))))'},
                "nonterminal"
            )

        return [obl_case]

    def handle_subgraphs(self, lemma, pos, clemma, cpos, dep, parent, i, j):
        parent_dep = parent[2]
        parent_pos = parent[1]

        subgraph = None

        if dep == "CONJ":
            return self.handle_conj(parent_pos, parent_dep, pos, cpos, i)

        if parent_dep == "ACL_RELCL":
            return self.handle_acl_relcl(parent_pos, pos, cpos, i, j)

        if parent_dep == "OBL":
            return self.handle_obl_case(parent_pos, pos, cpos, i, clemma)

        return subgraph

    def get_terminal_rules(self, word, pos, i):
        terminal_fss = self.get_default_terminal(word, i)

        return [terminal_fss]

    def get_default_binary_rule(self, dep):
        return f'f_dep1(merge(merge(?1,"(r<root> :{dep} (d1<dep1>))"), r_dep1(?2)))', f'f_dep1(merge(merge(?1,"(r<root> :UNKNOWN (d1<dep1>))"), r_dep1(?2)))'
