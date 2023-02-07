from xml.etree.ElementTree import fromstring

import requests
from ucca.convert import from_standard, split2sentences, to_text

from tuw_nlp.graph.ucca_graph import UCCAGraph

HOST = "localhost"
PORT = 5001


class TextToUCCA:
    def __init__(self, lang="en"):
        self.lang = lang

    def make_request(self, text):
        x = requests.post(
            f"http://{HOST}:{PORT}/parse",
            json={"text": text},
            headers={"Content-Type": "application/json"},
        )

        if x.status_code != 200:
            raise Exception(f"error {x.status_code}")
        else:
            return x.text

    def __call__(self, text):
        ucca_xml = self.make_request(text)
        doc_passage = from_standard(fromstring(ucca_xml))
        passages = split2sentences(doc_passage)

        for passage in passages:
            tokens = to_text(passage)[0].split()

            ucca_graph = UCCAGraph(passage, text, tokens)

            yield ucca_graph
