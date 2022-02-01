from stanza.models.common import doc
from stanza.pipeline.processor import Processor, register_processor

from tuw_nlp.text.patterns.de import ABBREV, MONTH


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

        if sen1.text.endswith(':'):
            return True, True

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

                sens[-1].append({
                    doc.ID: (token_id + 1, ),
                    doc.TEXT: token.text,
                    doc.MISC: token.misc,
                    doc.START_CHAR: token.start_char + char_offset,
                    doc.END_CHAR: token.end_char + char_offset})

                token_id += 1

        return doc.Document(sens, document.text)
