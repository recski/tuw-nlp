#!/bin/bash.
curl http://sandbox.hlt.bme.hu/~adaamko/alto-2.3.6-SNAPSHOT-all.jar --create-dirs -o ~/tuw_nlp_resources/alto-2.3.6-SNAPSHOT-all.jar
python -c 'import stanza; stanza.download("en", resources_version="1.1.0")'
python -c 'import stanza; stanza.download("de", resources_version="1.1.0")'
wget http://sandbox.hlt.bme.hu/~adaamko/definitions.zip
mkdir tuw_nlp/text/definitions
unzip definitions.zip -d tuw_nlp/text/
rm definitions.zip
python -m nltk.downloader stopwords
