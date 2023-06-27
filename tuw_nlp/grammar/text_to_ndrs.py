import requests

from tuw_nlp.graph.drs_graph import DRSGraph

HOST = "localhost"
PORT = 5002


class TextToNDRS:
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
            result = x.json()

            if result["result"]["errors"]:
                if 'graph' in result['result']:
                    assert result['result']['graph'] is None
                    return None
                else:
                    raise Exception(result["result"]["errors"])
            else:
                graph = result["result"]["graph"]
                return graph

    def __call__(self, text):
        cytoscape_graph = self.make_request(text)

        if cytoscape_graph is None:
            yield None
        else:
            graph = DRSGraph(cytoscape_graph, text, tokens_by_id=None)
            yield graph
