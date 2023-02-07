from conllu import parse
from supar import Parser

from tuw_nlp.graph.sdp_graph import SDPGraph
from tuw_nlp.text.pipeline import CustomStanzaPipeline


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

        sentence = str(dataset[0])
        sentence = self.preprocess_conllu(sentence)

        conllu_sentence = parse(str(sentence))[0]

        sdp_graph = SDPGraph(
            graph=conllu_sentence, text=text, tokens=tokens, type="sdp", lemmas=lemmas
        )

        yield sdp_graph

    def preprocess_conllu(self, connll_str):
        newlines = []
        lines = connll_str.split("\n")

        for line in lines:
            if line:
                values = line.split("\t")
                deps = values[8]
                if ":" in deps:
                    deps = deps.replace("_and_c", "and")
                    deps = deps.replace("_or_c", "or")
                values[8] = deps
                line = "\t".join(values)

                newlines.append(line)
            else:
                newlines.append(line)

        newconnll_str = "\n".join(newlines)

        return newconnll_str
