# TUW-NLP

NLP utilities developed at TUW informatics. 

## Install and Quick Start
Install the tuw-nlp repository from pip:

```
pip install tuw-nlp
```

Or install from source:
```
pip install -e .
```
![s](data:image/svg+xml,%3C%3Fxml%20version%3D%221.0%22%20encoding%3D%22UTF-8%22%20standalone%3D%22no%22%3F%3E%0A%3C!DOCTYPE%20svg%20PUBLIC%20%22-%2F%2FW3C%2F%2FDTD%20SVG%201.1%2F%2FEN%22%0A%20%22http%3A%2F%2Fwww.w3.org%2FGraphics%2FSVG%2F1.1%2FDTD%2Fsvg11.dtd%22%3E%0A%3C!--%20Generated%20by%20graphviz%20version%202.43.0%20(0)%0A%20--%3E%0A%3C!--%20Title%3A%20finite_state_machine%20Pages%3A%201%20--%3E%0A%3Csvg%20width%3D%2286pt%22%20height%3D%22186pt%22%0A%20viewBox%3D%220.00%200.00%2088.59%20191.59%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20xmlns%3Axlink%3D%22http%3A%2F%2Fwww.w3.org%2F1999%2Fxlink%22%3E%0A%3Cg%20id%3D%22graph0%22%20class%3D%22graph%22%20transform%3D%22scale(1.03%201.03)%20rotate(0)%20translate(4%20187.59)%22%3E%0A%3Ctitle%3Efinite_state_machine%3C%2Ftitle%3E%0A%3Cpolygon%20fill%3D%22white%22%20stroke%3D%22transparent%22%20points%3D%22-4%2C4%20-4%2C-187.59%2084.59%2C-187.59%2084.59%2C4%20-4%2C4%22%2F%3E%0A%3C!--%200%20--%3E%0A%3Cg%20id%3D%22node1%22%20class%3D%22node%22%3E%0A%3Ctitle%3E0%3C%2Ftitle%3E%0A%3Cellipse%20fill%3D%22none%22%20stroke%3D%22black%22%20cx%3D%2240.3%22%20cy%3D%22-157.59%22%20rx%3D%2226%22%20ry%3D%2226%22%2F%3E%0A%3Ctext%20text-anchor%3D%22middle%22%20x%3D%2240.3%22%20y%3D%22-153.89%22%20font-family%3D%22Times%2Cserif%22%20font-size%3D%2214.00%22%3Ehat%3C%2Ftext%3E%0A%3C%2Fg%3E%0A%3C!--%201%20--%3E%0A%3Cg%20id%3D%22node2%22%20class%3D%22node%22%3E%0A%3Ctitle%3E1%3C%2Ftitle%3E%0A%3Cellipse%20fill%3D%22none%22%20stroke%3D%22black%22%20cx%3D%2240.3%22%20cy%3D%22-40.3%22%20rx%3D%2240.09%22%20ry%3D%2240.09%22%2F%3E%0A%3Ctext%20text-anchor%3D%22middle%22%20x%3D%2240.3%22%20y%3D%22-36.6%22%20font-family%3D%22Times%2Cserif%22%20font-size%3D%2214.00%22%3Eyellow%3C%2Ftext%3E%0A%3C%2Fg%3E%0A%3C!--%200%26%2345%3B%26gt%3B1%20--%3E%0A%3Cg%20id%3D%22edge1%22%20class%3D%22edge%22%3E%0A%3Ctitle%3E0%26%2345%3B%26gt%3B1%3C%2Ftitle%3E%0A%3Cpath%20fill%3D%22none%22%20stroke%3D%22black%22%20d%3D%22M40.3%2C-131.57C40.3%2C-119.64%2040.3%2C-104.91%2040.3%2C-90.85%22%2F%3E%0A%3Cpolygon%20fill%3D%22black%22%20stroke%3D%22black%22%20points%3D%2243.8%2C-90.77%2040.3%2C-80.77%2036.8%2C-90.77%2043.8%2C-90.77%22%2F%3E%0A%3Ctext%20text-anchor%3D%22middle%22%20x%3D%2245.3%22%20y%3D%22-102.39%22%20font-family%3D%22Times%2Cserif%22%20font-size%3D%2214.00%22%3E0%3C%2Ftext%3E%0A%3C%2Fg%3E%0A%3C%2Fg%3E%0A%3C%2Fsvg%3E%0A)

On Windows and Mac, you might also need to install [Graphviz](https://graphviz.org/download/) manually.

You will also need some additional steps to use the library:

Download nltk stopwords:

```python
import nltk
nltk.download('stopwords')
```

Download stanza models for UD parsing:

```python
import stanza

stanza.download("en")
stanza.download("de")
```

And then finally download ALTO and tuw_nlp dictionaries:
```python
import tuw_nlp

tuw_nlp.download_alto()
tuw_nlp.download_definitions()
```

__Also please make sure to have JAVA on your system to be able to use the parser!__

Then you can parse a sentence as simple as:

```python
from tuw_nlp.grammar.text_to_4lang import TextTo4lang

tfl = TextTo4lang("en", "en_nlp_cache")

fl_graphs = list(tfl("brown dog", depth=1, substitute=False))

# Then the fl_graphs will directly contain a networkx graph object
fl_graphs[0].nodes(data=True)

```
For more examples you can check the jupyter notebook under *notebooks/experiment*

## Services

We also provide services built on our package. To get to know more visit [services](services).

### Text_to_4lang service

To run a browser-based demo (also available [online](https://ir-group.ec.tuwien.ac.at/fourlang)) for building graphs from raw texts, first start the graph building service:

```
python services/text_to_4lang/backend/service.py
```

Then run the frontend with this command:

```
streamlit run services/text_to_4lang/frontend/extract.py
```

In the demo you can parse english and german sentences and you can also try out multiple algorithms our graphs implement, such as `expand`, `substitute` and `append_zero_paths`.

## Modules

### text 

General text processing utilities, contains:
- segmentation: stanza-based processors for word and sentence level segmentation
- patterns: various patterns for text processing tasks 

### graph
Tools for working with graphs, contains:
- utils: misc utilities for working with graphs

### grammar
Tools for generating and using grammars, contains:
- alto: tools for interfacing with the [alto](https://github.com/coli-saar/alto) tool
- irtg: class for representing Interpreted Regular Tree Grammars
- lexicon: Rule lexica for building lexicalized grammars
- ud_fl: grammar-based mapping of [Universal Dependencies](https://universaldependencies.org/) to [4lang](https://github.com/kornai/4lang) semantic graphs.
- utils: misc utilities for working with grammars

## Contributing

We welcome all contributions! Please fork this repository and create a branch for your modifications. We suggest getting in touch with us first, by opening an issue or by writing an email to Gabor Recski or Adam Kovacs at firstname.lastname@tuwien.ac.at

## Citing

If you use the library, please cite our [paper](http://ceur-ws.org/Vol-2888/paper3.pdf)

```bib
@inproceedings{Recski:2021,
  title={Explainable Rule Extraction via Semantic Graphs},
  author={Recski, Gabor and Lellmann, Bj{\"o}rn and Kovacs, Adam and Hanbury, Allan},
  booktitle = {{Proceedings of the Fifth Workshop on Automated Semantic Analysis
of Information in Legal Text (ASAIL 2021)}},
  publisher = {{CEUR Workshop Proceedings}},
  address = {São Paulo, Brazil},
  pages="24--35",
  url= "http://ceur-ws.org/Vol-2888/paper3.pdf",
  year={2021}
}
```

## License 

MIT license
