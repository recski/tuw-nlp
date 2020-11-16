import json

from stanza.models.common.doc import Document as StanzaDocument


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
