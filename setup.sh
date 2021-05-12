#!/bin/bash.
wget -nc http://sandbox.hlt.bme.hu/~adaamko/alto-2.3.6-SNAPSHOT-all.jar
python -c 'import stanza; stanza.download("en")'
python -c 'import stanza; stanza.download("de")'
wget http://sandbox.hlt.bme.hu/~adaamko/definitions.zip
mkdir tuw_nlp/text/definitions
unzip definitions.zip -d tuw_nlp/text/
rm definitions.zip
python -m nltk.downloader stopwords