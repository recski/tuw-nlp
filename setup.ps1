mkdir ~/tuw_nlp_resources
wget http://sandbox.hlt.bme.hu/~adaamko/alto-2.3.6-SNAPSHOT-all.jar -OutFile ~/tuw_nlp_resources/alto-2.3.6-SNAPSHOT-all.jar
python -m downloadstanza.py
wget http://sandbox.hlt.bme.hu/~adaamko/definitions.zip -OutFile definitions.zip
mkdir tuw_nlp/text/definitions
Expand-Archive -Path definitions.zip -DestinationPath tuw_nlp/text/
rm definitions.zip
python -m nltk.downloader stopwords
