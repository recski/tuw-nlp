from tuw_nlp.text.segmentation import CustomStanzaPipeline


def test_stanza_pipeline():
    nlp = CustomStanzaPipeline(processors='tokenize,pos,lemma,depparse')
    doc = nlp('Dachgeschosse sind nicht zulässig.')
    assert 'head' in doc.sentences[0].to_dict()[0]
