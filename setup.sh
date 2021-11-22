#!/bin/bash.
curl http://sandbox.hlt.bme.hu/~adaamko/definitions.zip -o definitions.zip
mkdir tuw_nlp/text/definitions
unzip definitions.zip -d tuw_nlp/text/
rm definitions.zip
