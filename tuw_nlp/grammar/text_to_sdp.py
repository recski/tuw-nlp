from supar import Parser
from tuw_nlp.text.pipeline import CustomStanzaPipeline
from tuw_nlp.graph.sdp_graph import SDPGraph
from conllu import parse


class TextToSDP:
    """
    Convert text to SDP.
    """

    def __init__(self, lang="en"):
        assert lang == "en", "TextToSDP only supports english currently"
        self.sdp = Parser.load("biaffine-sdp-en")

        self.nlp = CustomStanzaPipeline(
            "en", processors="tokenize,mwt,pos,lemma,depparse"
        )

    def __call__(self, text):
        sdp_input = []
        doc = self.nlp(text)
        tokens = []
        lemmas = []

        for sen in doc.sentences:
            sen_wlp = []
            for word in sen.to_dict():
                sen_wlp.append((word["text"], word["lemma"], word["upos"]))
                tokens.append(word["text"])
                lemmas.append(word["lemma"])
            sdp_input.append(sen_wlp)

        dataset = self.sdp.predict(sdp_input, verbose=False)

        sentence = dataset[0]

        conllu_sentence = parse(str(sentence))[0]

        sdp_graph = SDPGraph(
            graph=conllu_sentence, text=text, tokens=tokens, type="sdp", lemmas=lemmas
        )

        yield sdp_graph
