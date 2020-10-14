import stanza
from tuw_nlp.text.segmentation import CustomStanzaPipeline
from tuw_nlp.grammar.ud_fl import UD_FL, UD_Fourlang

en_nlp = stanza.Pipeline('en')

def test_ud_fl():
    text = 'Dachgeschosse sind nicht zulässig.'
    ud_fl = UD_FL()
    nlp = CustomStanzaPipeline(processors='tokenize,pos,lemma,depparse')
    sen = nlp(text).sentences[0]
    fl = ud_fl.parse(sen, 'ud', 'fl', 'amr-sgraph-src')
    assert fl == "(u_1<root> / PER  :1 (u_3 / Dachgeschosse))"

def test_ud_fourlang_en():
    text = 'I have a dog.'
    ud_fl = UD_Fourlang()
    nlp = stanza.Pipeline('en')
    sen = nlp(text).sentences[0]
    fl = ud_fl.parse(sen, 'ud', 'fourlang', 'amr-sgraph-src')
    assert fl == "(u_1<root> / PER  :1 (u_3 / Dachgeschosse))"


if __name__ == "__main__":
    test_ud_fourlang_en()
