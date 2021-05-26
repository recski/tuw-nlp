import json

from stanza.models.common.doc import Document as StanzaDocument
from stanza.utils.conll import CoNLL

from tuw_nlp.text.patterns.misc import (
    EMOJI_PATT, TWITTER_USERNAME_PATT, TWITTER_HASHTAG_PATT)


def gen_tsv_sens(stream, swaps=()):
    curr_sen = []
    for raw_line in stream:
        line = raw_line.strip()
        if line.startswith("#"):
            continue
        if not line:
            yield curr_sen
            curr_sen = []
            continue
        fields = line.split('\t')
        for i, j in swaps:
            fields[i], fields[j] = fields[j], fields[i]
        curr_sen.append(fields)


def gen_conll_sens(stream, swaps=()):
    for sen in gen_tsv_sens(stream, swaps):
        dic = CoNLL.convert_conll([sen])
        yield StanzaDocument(dic).sentences[0]


def gen_conll_sens_from_file(fn, swaps=()):
    with open(fn, "r") as f:
        yield from gen_conll_sens(f, swaps)


def print_conll_sen(sen, sent_id=None, swaps=()):
    out = f'# sent_id = {sent_id}\n# text = {sen.text}\n'
    for fields in CoNLL.convert_dict([sen.to_dict()])[0]:
        for i, j in swaps:
            fields[i], fields[j] = fields[j], fields[i]
        out += "\t".join(fields) + '\n'
    return out


def normalize_whitespace(text):
    nt = text.strip()
    if nt == "":
        return ""
    return " ".join([s for s in text.split() if s])


def load_parsed(fn):
    with open(fn) as f:
        parsed = json.load(f)
        return {
            doc_id: StanzaDocument(parse) for doc_id, parse in parsed.items()}


def save_parsed(parsed, fn):
    with open(fn, 'w') as f:
        json.dump(
            {doc_id: doc.to_dict() for doc_id, doc in parsed.items()}, f)


def replace_emojis(text, with_what='EMOJI'):
    return EMOJI_PATT.sub(with_what, text)


def preprocess_tweet(text, keep_username=False, keep_hashtag=False):
    user_sub = r"\1" if keep_username else r""
    hashtag_sub = r"\1" if keep_hashtag else r""
    tweet = TWITTER_USERNAME_PATT.sub(user_sub, text)
    tweet = TWITTER_HASHTAG_PATT.sub(hashtag_sub, tweet)
    tweet = normalize_whitespace(tweet)
    return tweet
