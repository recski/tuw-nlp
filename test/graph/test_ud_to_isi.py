from tuw_nlp.text.pipeline import CustomStanzaPipeline
from tuw_nlp.graph.utils import graph_to_isi, sen_to_graph


def test_ud_graph_to_isi():
    nlp = CustomStanzaPipeline(processors='tokenize,pos,lemma,depparse')
    doc = nlp('Dachgeschosse sind nicht zulässig.')
    graph = sen_to_graph(doc.sentences[0])
    isi = graph_to_isi(graph)
    assert isi == 'ROOT(ADJ(_NSUBJ(NOUN(Dachgeschosse)), ADJ(_COP(AUX(sein)), ADJ(_ADVMOD(PART(nicht)), ADJ(_PUNCT(PUNCT(PERIOD)), ADJ(zulaessig))))))'  # noqa


if __name__ == "__main__":
    test_ud_graph_to_isi()
