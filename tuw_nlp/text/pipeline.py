import os

import stanza

from tuw_nlp.text import segmentation  # noqa
from tuw_nlp.text.utils import load_parsed, save_parsed


class CustomStanzaPipeline():
    def __init__(self, lang='de', processors=None):
        assert lang == 'de', "CustomStanzaTokenizer only supports German"
        self.tokenizer = stanza.Pipeline(
            lang='de', processors='tokenize,fix_ssplit')
        self.additional = stanza.Pipeline(
            lang='de', processors=processors, tokenize_no_ssplit=True)

    def ssplit(self, text):
        return [sen.text for sen in self.tokenizer(text).sentences]

    def process(self, text):
        sens = self.ssplit(text)
        return self.additional("\n\n".join(sens))

    def __call__(self, text):
        return self.process(text)


class CachedStanzaPipeline():
    def __init__(self, stanza_pipeline, cache_path):
        self.nlp = stanza_pipeline
        self.cache_path = cache_path
        if os.path.exists(self.cache_path):
            self.parsed = load_parsed(self.cache_path)
        else:
            self.parsed = {}

    def __call__(self, text):
        if text not in self.parsed:
            self.parsed[text] = self.nlp(text)

        return self.parsed[text]

    def __enter__(self):
        return self

    def __exit__(self):
        save_parsed(self.parsed, self.cache_path)
