#!/bin/bash.
python -m downloadstanza.py
curl http://sandbox.hlt.bme.hu/~adaamko/definitions.zip -o definitions.zip
mkdir tuw_nlp/text/definitions
unzip definitions.zip -d tuw_nlp/text/
rm definitions.zip
python -m nltk.downloader stopwords
