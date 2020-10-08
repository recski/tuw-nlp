from tuw_nlp.text.segmentation import CustomStanzaPipeline
from tuw_nlp.grammar.ud_fl import UD_FL


def test_ud_fl():
    text = 'Dachgeschosse sind nicht zulässig.'
    ud_fl = UD_FL()
    nlp = CustomStanzaPipeline(processors='tokenize,pos,lemma,depparse')
    sen = nlp(text).sentences[0]
    fl = ud_fl.parse(sen, 'ud', 'fl', 'amr-sgraph-src')
    assert fl == "(u_1<root> / PER  :1 (u_3 / Dachgeschosse))"
