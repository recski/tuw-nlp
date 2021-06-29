import json
import re
import requests
import networkx
import networkx as nx
import streamlit as st
from networkx.readwrite import json_graph

HOST = "http://localhost"
PORT = 5006


def d_clean(string):
    s = string
    for c in '\\=@-,\'".!:;<>/{}[]()#^?':
        s = s.replace(c, '_')
    s = s.replace('$', '_dollars')
    s = s.replace('%', '_percent')
    s = s.replace('|', ' ')
    s = s.replace('*', ' ')
    if s == '#':
        s = '_number'
    keywords = ("graph", "node", "strict", "edge")
    if re.match('^[0-9]', s) or s in keywords:
        s = "X" + s
    return s

def to_dot(graph, marked_nodes=set()):
    lines = [u'digraph finite_state_machine {', '\tdpi=70;']
    # lines.append('\tordering=out;')
    # sorting everything to make the process deterministic
    node_lines = []
    for node, n_data in graph.nodes(data=True):
        d_node = d_clean(node)
        printname = d_clean('_'.join(d_node.split('_')[:-1]))
        if 'expanded' in n_data and n_data['expanded'] and printname in marked_nodes:
            node_line = u'\t{0} [shape = circle, label = "{1}", \
                    style=filled, fillcolor=purple];'.format(
                d_node, printname).replace('-', '_')
        elif 'expanded' in n_data and n_data['expanded']:
            node_line = u'\t{0} [shape = circle, label = "{1}", \
                    style="filled"];'.format(
                d_node, printname).replace('-', '_')
        elif 'fourlang' in n_data and n_data['fourlang']:
            node_line = u'\t{0} [shape = circle, label = "{1}", \
                    style="filled", fillcolor=red];'.format(
                d_node, printname).replace('-', '_')
        elif 'substituted' in n_data and n_data['substituted']:
            node_line = u'\t{0} [shape = circle, label = "{1}", \
                    style="filled"];'.format(
                d_node, printname).replace('-', '_')
        elif printname in marked_nodes:
            node_line = u'\t{0} [shape = circle, label = "{1}", style=filled, fillcolor=lightblue];'.format(
                d_node, printname).replace('-', '_')
        else:
            node_line = u'\t{0} [shape = circle, label = "{1}"];'.format(
                d_node, printname).replace('-', '_')
        node_lines.append(node_line)
    lines += sorted(node_lines)

    edge_lines = []
    for u, v, edata in graph.edges(data=True):
        if 'color' in edata:
            d_node1 = d_clean(u)
            d_node2 = d_clean(v)
            edge_lines.append(
                u'\t{0} -> {1} [ label = "{2}" ];'.format(
                    d_clean(d_node1), d_clean(d_node2),
                    edata['color']))

    lines += sorted(edge_lines)
    lines.append('}')
    return u'\n'.join(lines)

@st.cache
def build(text, method, depth, lang, append):
    host = f'{HOST}:{PORT}'
    data_json = json.dumps({"text": text, "method": method, "depth": depth, "lang": lang, "append": append})
    headers = {
        'Content-type': 'application/json',
    }
    r = requests.post(host + '/build', data=data_json, headers=headers)
    result = r.json()["result"]

    return result

def get_definition(word, lang):
    host = f'{HOST}:{PORT}'
    data_json = json.dumps({"text": word, "lang": lang})
    headers = {
        'Content-type': 'application/json',
    }
    r = requests.post(host + '/get_definition', data=data_json, headers=headers)
    result = r.json()["result"]

    return result


def main():
    st.sidebar.title("Select the parameters")
    method = st.sidebar.selectbox("Select Method", ["expand", "substitute"])
    lang = st.sidebar.selectbox("Select Language", ["en", "de"])
    depth = st.sidebar.number_input("Select Recursion depth", format="%i", value=0, min_value=0, max_value=3)
    append_zero_graph = st.sidebar.checkbox('Append zero paths')
    word = st.sidebar.text_input("Get definition of a word: ")
    st.title("Build Fourlang graph from text")

    text = st.text_area("Input your own text here")

    result = build(text, method, depth, lang, append_zero_graph)
    
    if not result["errors"]:
        dot = result["graph"]
        ud_graph = result["ud"]
        
        st.text(f'UD graph:')
        #dot = json_graph.adjacency_graph(ph
        st.graphviz_chart(ud_graph, use_container_width=True)
        st.text(f'Fourlang graph:')
        st.graphviz_chart(dot, use_container_width=True)

    if word:
        definition = get_definition(word, lang)
        if definition:
            st.text(definition["def"])

if __name__ == "__main__":
    main()
