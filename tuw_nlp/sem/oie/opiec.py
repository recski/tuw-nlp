import json
import pdb
import sys

from avro.datafile import DataFileReader
from avro.io import DatumReader


AVRO_SCHEMA_FILE, AVRO_FILE = sys.argv[1:3]
reader = DataFileReader(open(AVRO_FILE, "rb"), DatumReader())
for triple in reader:
    print(json.dumps(triple))
    # use triple.keys() to see every field in the schema (it's a dictionary)
    # pdb.set_trace()
reader.close()
