import requests

HOST = "localhost"
PORT = 5002

class TextToDRS:
    def __init__(self, language='en'):
        self.language = language

    def make_request(self, text):
        x = requests.post(
            f"http://{HOST}:{PORT}/parse",
            json={"text": text},
            headers={"Content-Type": "application/json"},
        )

        if x.status_code != 200:
            raise Exception(f"error {x.status_code}")
        else:
            return x.graph

    