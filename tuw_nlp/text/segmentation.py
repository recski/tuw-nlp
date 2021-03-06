import stanza
from stanza.models.common import doc
from stanza.pipeline.processor import Processor, register_processor

from tuw_nlp.text.patterns.de import ABBREV, MONTH
from tuw_nlp.text.patterns.misc import CHAR_PATT


@register_processor("fix_ssplit")
class SsplitFixer(Processor):
    ''' Fixes erroneous sentence splits of the German Stanza model '''
    _requires = set(['tokenize'])
    _provides = set(['fix_ssplit'])

    def __init__(self, config, pipeline, use_gpu):
        pass

    def _set_up_model(self, *args):
        pass

    def is_err(self, sen1, sen2):
        """determine if the split between sen1 and sen2 was an error"""
        for abbr in ABBREV:
            if sen1.text.endswith(f' {abbr}'):
                return True, True

        for month in MONTH:
            if sen2.text.startswith(month):
                return True, True

        return False, None

    def process(self, document):
        sens = []
        char_offset = 0
        new_sen = True
        for i, sentence in enumerate(document.sentences):
            if new_sen:
                token_id = 0
                sens.append([])
                new_sen = False
            for token in sentence.tokens:
                if token is sentence.tokens[-1] and not (
                        sentence is document.sentences[-1]):

                    is_err, requires_space = self.is_err(
                        sentence, document.sentences[i+1])
                    if not is_err:
                        new_sen = True
                    else:
                        if requires_space is False:
                            char_offset -= 1

                start_char, end_char = (
                    int(c) + char_offset
                    for c in CHAR_PATT.match(token.misc).groups())

                sens[-1].append({
                    doc.ID: (token_id + 1, ), doc.TEXT: token.text,
                    doc.MISC: f'start_char={start_char}|end_char={end_char}'})

                token_id += 1

        return doc.Document(sens, document.text)


class CustomStanzaPipeline():
    def __init__(self, lang='de', processors=None):
        assert lang == 'de', "CustomStanzaTokenizer only supports German"
        self.tokenizer = stanza.Pipeline(
            lang='de', processors='tokenize,fix_ssplit')
        self.additional = stanza.Pipeline(
            lang='de', processors=processors, tokenize_pretokenized=True)

    def ssplit(self, text):
        return [sen.text for sen in self.tokenizer(text).sentences]

    def process(self, text):
        return self.additional([
            [word.text for word in sen.words]
            for sen in self.tokenizer(text).sentences])

    def __call__(self, text):
        return self.process(text)
