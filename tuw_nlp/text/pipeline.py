import os

import stanza

from tuw_nlp import logger
from tuw_nlp.text import segmentation  # noqa
from tuw_nlp.text.utils import load_parsed, save_parsed


class CustomStanzaPipeline:
    def __init__(self, lang="de", processors=None, package="default"):
        if processors is None:
            processors = {}
        self.lang = lang

        if self.lang == "de":
            self.tokenizer = stanza.Pipeline(
                lang="de", processors="tokenize,fix_ssplit"
            )
        else:
            self.tokenizer = stanza.Pipeline(
                lang=self.lang, processors="tokenize", package=package
            )

        self.additional = stanza.Pipeline(
            lang=self.lang,
            processors=processors,
            tokenize_no_ssplit=True,
            package=package,
        )

    def ssplit(self, text):
        return [sen.text for sen in self.tokenizer(text).sentences]

    def process(self, text):
        sens = self.ssplit(text)
        return self.additional("\n\n".join(sens))

    def __call__(self, text):
        return self.process(text)


class CachedStanzaPipeline:
    def __init__(self, stanza_pipeline, cache_path, init=None):
        if stanza_pipeline is None:
            assert init is not None

        self.nlp = stanza_pipeline
        self.init = init
        self.cache_path = cache_path
        if os.path.exists(self.cache_path):
            logger.info(f"loading NLP cache from {self.cache_path}...")
            self.parsed = load_parsed(self.cache_path)
            logger.info("done!")
        else:
            self.parsed = {}
            logger.info(f"creating new NLP cache in {self.cache_path}")

        self.changed = False

    def parse(self, text, ssplit):
        if self.nlp is None:
            self.nlp = self.init()

        return self.nlp(text) if ssplit else self.nlp.additional(text)

    def __call__(self, text, ssplit=True):
        if text not in self.parsed:
            self.parsed[text] = self.parse(text, ssplit=ssplit)
            self.changed = True

        return self.parsed[text]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.changed:
            logger.info(f"saving NLP cache to {self.cache_path}...")
            save_parsed(self.parsed, self.cache_path)
            logger.info("done!")
