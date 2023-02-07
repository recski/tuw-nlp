# TUW-NLP

NLP utilities developed at TUW informatics. 

The main goal of the library is to provide a unified interface for working with different semantic graph representations. To represent 
graphs we use the [networkx](https://networkx.org/) library.
Currently you can use the following semantic graph representations integrated in the library:
- [4lang](#4lang)
- [UD](#ud) (Universal Dependencies)
- [AMR](#amr) (Abstract Meaning Representation)
- [SDP](#sdp) (Semantic Dependency Parsing)
- [UCCA](#ucca) (Universal Conceptual Cognitive Annotation)
- [DRS](#drs) (Discourse Representation Structure)

## Setup and Usage
Install the tuw-nlp repository from pip:

```
pip install tuw-nlp
```

Or install from source:
```
pip install -e .
```

On Windows and Mac, you might also need to install [Graphviz](https://graphviz.org/download/) manually.

You will also need some additional steps to use the library:

Download nltk resources:

```python
import nltk
nltk.download('stopwords')
nltk.download('propbank')
```

Download stanza models for UD parsing:

```python
import stanza

stanza.download("en")
stanza.download("de")
```

### 4lang

The [4lang](https://github.com/kornai/4lang) semantic graph representation is implemented in the repository. We use Interpreted Regular Tree Grammars (IRTGs) to build the graphs from UD trees. The grammar can be found in the [lexicon](tuw_nlp/grammar/lexicon.py). It supports English and German.

To use the parser download the [alto](https://github.com/coli-saar/alto) parser and tuw_nlp dictionaries:

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

# Then the fl_graphs are the classes that contains the networkx graph object
fl_graphs[0].G.nodes(data=True)

# Visualize the graph
fl_graphs[0].to_dot()

```

### UD
To parse [Universal Dependencies](https://universaldependencies.org/)
into networkx format, we use the [stanza](https://stanfordnlp.github.io/stanza/) library. You can use all the languages supported by stanza:
https://stanfordnlp.github.io/stanza/models.html

For parsing you can use the snippet above, just use the `TextToUD` class.

### AMR
For parsing [Abstract Meaning Representation](https://amr.isi.edu/) graphs we use the [amrlib](https://amrlib.readthedocs.io/en/latest/) library. Models are only available for English.

If you want to use AMR parsing, install the [amrlib](https://amrlib.readthedocs.io/en/latest/) package (this is also included in the __setup__ file) and download the models:

```bash
pip install amrlib
```

Go to the [amrlib](https://amrlib.readthedocs.io/en/latest/) repository and follow the instructions to download the models. 

Then also download the spacy model for AMR parsing:

```bash
python -m spacy download en_core_web_sm
```

To parse AMR, see the `TextToAMR` class.

### SDP
For parsing [Semantic Dependency Parsing](https://aclanthology.org/S15-2153/) we integrated the Semantic Dependency Parser from the [SuPar](https://github.com/yzhangcs/parser) library. Models are only available for English. 

See the `TextToSDP` class for more information.

### UCCA
For parsing [UCCA](https://github.com/UniversalConceptualCognitiveAnnotation/tutorial) graphs we integrated the __tupa__ parser. See our fork of the parser [here](https://github.com/adaamko/tupa). Because of the complexity of the parser, we included a docker image that contains the parser and all the necessary dependencies. You can use the docker image to parse UCCA graphs. To see more go to the [services](services/ucca_service/) folder and follow the instructions there.

UCCA parsing is currently supporting English, French, German and Hebrew. The docker service is a REST API that you can use to parse UCCA graphs. To convert the output to networkx graphs, see the `TextToUCCA` class.

### DRS
The task of __Discourse Representation Structure (DRS) parsing__ is to convert text into formal meaning representations in the style of Discourse Representation Theory (DRT; Kamp and Reyle 1993). 

To make it compatible with our library, we make use of the paper titled [Transparent Semantic Parsing with Universal Dependencies Using Graph Transformations](https://aclanthology.org/2022.coling-1.367/). This work first transformes DRS structures into graphs (DRG). They make use of a rule-based method developed using the [GREW](https://grew.fr) library.

Because of the complexity of the parser, we included a docker image that contains the parser and all the necessary dependencies. You can use the docker image to parse DRS graphs. To see more go to the [services](services/boxer_service/) folder and follow the instructions there. For parsing we our own fork of the [ud-boxer](https://github.com/adaamko/ud-boxer) repository. Currently it supports English, Italian, German and Dutch.

To convert the output of the REST API (from the docker service) to networkx graphs, see the `TextToDRS` class.

For more examples you can check our [experiments](notebooks/experiments.ipynb) jupyter notebook.

### Command line interface

We provide a simple script to parse into any of the supported formats.
For this you can use the `scripts/semparse.py` script. For usage:

```bash
usage: semparse.py [-h] [-f FORMAT] [-cd CACHE_DIR] [-cn NLP_CACHE] -l LANG [-d DEPTH] [-s SUBSTITUTE] [-p PREPROCESSOR] [-o OUT_DIR]

optional arguments:
  -h, --help            show this help message and exit
  -f FORMAT, --format FORMAT
  -cd CACHE_DIR, --cache-dir CACHE_DIR
  -cn NLP_CACHE, --nlp-cache NLP_CACHE
  -l LANG, --lang LANG
  -d DEPTH, --depth DEPTH
  -s SUBSTITUTE, --substitute SUBSTITUTE
  -p PREPROCESSOR, --preprocessor PREPROCESSOR
  -o OUT_DIR, --out-dir OUT_DIR
```

For example to parse a sentence into UCCA graph run:
  
  ```bash
  echo "A police statement did not name the man in the boot, but in effect indicated the traveler was State Secretary Samuli Virtanen, who is also the deputy to Foreign Minister Timo Soini." | python scripts/semparse.py -f ucca -l en -cn cache/nlp_cache_en.json
  ```

## Services

We also provide services built on our package. To get to know more visit [services](services).

### Text_to_4lang service

To run a browser-based demo (also available [online](https://ir-group.ec.tuwien.ac.at/fourlang)) for building graphs from raw texts, first start the graph building service:

```
python services/text_to_4lang/backend/service.py
```

Then run the frontend with this command:

```
streamlit run services/text_to_4lang/frontend/demo.py
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
