import stanza
from tuw_nlp.text.pipeline import CustomStanzaPipeline
from tuw_nlp.grammar.ud_fl import UD_FL
from tuw_nlp.graph.utils import read_alto_output


def test_ud_fl():
    text = 'Dachgeschosse sind nicht zulässig.'
    ud_fl = UD_FL(lang="de")
    nlp = CustomStanzaPipeline(processors='tokenize,pos,lemma,depparse')
    sen = nlp(text).sentences[0]
    fl = ud_fl.parse(sen, 'ud', 'fl', 'amr-sgraph-src')
    assert fl == "(u_1<root> / PER  :0 (u_3 / NEG)  :1 (u_6 / Dachgeschosse))"

def test_ud_fourlang_en():
    text = 'I have a dog.'
    ud_fl = UD_FL(lang="en")
    nlp = stanza.Pipeline('en')
    sen = nlp(text).sentences[0]
    fl = ud_fl.parse(sen, 'ud', 'fl', 'amr-sgraph-src')
    assert fl == "(u_1<root> / have  :2 (u_3 / dog)  :1 (u_6 / I))"


if __name__ == "__main__":
    test_ud_fl()
    test_ud_fourlang_en()
