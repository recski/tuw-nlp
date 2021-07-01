import datetime
import json
import sys
import traceback

import graphviz
import stanza
from flask import Flask, request
from graphviz import Source
import networkx as nx
from networkx.readwrite import json_graph
from tuw_nlp.grammar.text_to_4lang import TextTo4lang
from tuw_nlp.graph.fourlang import FourLang
from tuw_nlp.graph.utils import graph_to_pn
from tuw_nlp.text.pipeline import CachedStanzaPipeline, CustomStanzaPipeline

HOST = 'localhost'
PORT = 5006
app = Flask(__name__)

nlp = stanza.Pipeline('en')

nlp_de = CustomStanzaPipeline(processors='tokenize,pos,lemma,depparse')

text_to_4lang_en = TextTo4lang("en", "en_nlp_cache")
text_to_4lang_de = TextTo4lang("de", "de_nlp_cache")

# echo '0 Die Gebäudehöhe darf 6,5 m nicht überschreiten.' | python brise_nlp/plandok/get_attributes.py


def visualize(sentence):
    dot = graphviz.Digraph()
    dot.node("0", "ROOT", shape="box")
    for token in sentence.tokens:
        for word in token.words:
            dot.node(str(word.id), word.text)
            dot.edge(str(word.head), str(word.id),
                     label=word.deprel)
    return dot


@app.route('/build', methods=['POST'])
def build():
    ret_value = {"result": {"errors": None, "graph": None, "ud": None}}
    data = request.get_json()

    if len(data) == 0 or not data["text"]:
        print("No input text found")
        ret_value["result"]["errors"] = "No input text found"
        sys.stdout.flush()
        return json.dumps(ret_value)

    print("Text to process: {0}".format(data))

    try:
        lang = data["lang"] if "lang" in data else "en"
        text = data["text"]
        substitute = data["method"] == "substitute"
        depth = data["depth"]
        append_zero_graph = data["append"]
        if lang == "en":
            fl_graphs = list(text_to_4lang_en(text))
            g = fl_graphs[0]
            for n in fl_graphs[1:]:
                g = nx.compose(g, n)
            fl = FourLang(g, 0)
            if int(depth):
                text_to_4lang_en.expand(
                    fl, depth=int(depth), substitute=substitute)
            sen = nlp(text).sentences[0]
        elif lang == "de":
            fl_graphs = list(text_to_4lang_de(text))
            g = fl_graphs[0]
            for n in fl_graphs[1:]:
                g = nx.compose(g, n)
            fl = FourLang(g, 0)
            if int(depth):
                text_to_4lang_de.expand(
                    fl, depth=int(depth), substitute=substitute)
            sen = nlp_de(text).sentences[0]
        ret_value["result"]["ud"] = visualize(sen).source
        if fl:
            if append_zero_graph:
                fl.append_zero_paths()
            ret_value["result"]["graph"] = fl.to_dot()
    except Exception as e:
        traceback.print_exc()
        ret_value["result"]["errors"] = str(e)

    print("Returning: {0}".format(ret_value))
    sys.stdout.flush()
    return json.dumps(ret_value)


@app.route('/get_definition', methods=['POST'])
def get_definition():
    ret_value = {"result": {"errors": None, "def": None}}
    data = request.get_json()

    if len(data) == 0 or not data["text"]:
        print("No input text found")
        ret_value["result"]["errors"] = "No input text found"
        sys.stdout.flush()
        return json.dumps(ret_value)

    print("Text to process: {0}".format(data))

    try:
        text = data["text"]
        lang = data["lang"]

        if lang == "de":
            definition = text_to_4lang_de.lexicon.get_definition(text)
        else:
            definition = text_to_4lang_en.lexicon.get_definition(text)

        if definition:
            ret_value["result"]["def"] = definition
    except Exception as e:
        traceback.print_exc()
        ret_value["result"]["errors"] = str(e)

    print("Returning: {0}".format(ret_value))
    sys.stdout.flush()
    return json.dumps(ret_value)


if __name__ == '__main__':
    app.run(debug=True, host=HOST, port=PORT)
