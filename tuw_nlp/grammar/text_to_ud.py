from tuw_nlp.graph.ud_graph import UDGraph
from tuw_nlp.text.pipeline import CachedStanzaPipeline, CustomStanzaPipeline


class TextToUD:
    def __init__(self, lang, nlp_cache, cache_dir=None):
        if lang == "de":
            nlp = CustomStanzaPipeline(processors="tokenize,mwt,pos,lemma,depparse")
        elif lang == "en":
            nlp = CustomStanzaPipeline(
                "en", processors="tokenize,mwt,pos,lemma,depparse"
            )
        elif lang == "en_bio":
            nlp = CustomStanzaPipeline("en", package="craft")
        assert lang, "TextTo4lang does not have lang set"

        self.lang = lang

        self.nlp = CachedStanzaPipeline(nlp, nlp_cache)

    def __call__(self, text, ssplit=True):
        for sen in self.nlp(text, ssplit=ssplit).sentences:
            tokens = [token.text for token in sen.tokens]

            ud_graph = UDGraph(sen, text, tokens)

            yield ud_graph
