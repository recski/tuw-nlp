#!/bin/bash.
curl http://sandbox.hlt.bme.hu/~adaamko/alto-2.3.6-SNAPSHOT-all.jar --create-dirs -o ~/tuw_nlp_resources/alto-2.3.6-SNAPSHOT-all.jar
python -m downloadstanza.py
wget http://sandbox.hlt.bme.hu/~adaamko/definitions.zip
mkdir tuw_nlp/text/definitions
unzip definitions.zip -d tuw_nlp/text/
rm definitions.zip
python -m nltk.downloader stopwords
