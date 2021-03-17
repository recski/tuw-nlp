#!/bin/bash.
wget -nc http://sandbox.hlt.bme.hu/~adaamko/alto-2.3.6-SNAPSHOT-all.jar
python -c 'import stanza; stanza.download("en")'
python -c 'import stanza; stanza.download("de")'