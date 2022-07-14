# UCCA service

We provide a docker service for UCCA. The service is built on the [Transition-based UCCA parser](https://aclanthology.org/P17-1104/). 

Our fork can be found at: https://github.com/adaamko/tupa

The docker service can be started with __docker-compose__:
    
```
docker-compose up
```

The service is available at: http://localhost:5001/parse

Then you can make a post request to parse a text into UCCA:
        
```
curl -X POST -H "Content-Type: application/json" -d '{"text": "The cat is on the table."}' http://localhost:5001/parse
```

The response will be an XML object with the parsed graph.


You can also manually start the service if you don't prefer to use docker:

  1. Go to our fork and clone it: https://github.com/adaamko/tupa
  2. Create a conda environment with python 3.6: conda create -n tupa python=3.6
  3. With this environment, install tupa: pip install tupa
  4. Download and extract pretrained models: 
```
curl -LO https://github.com/huji-nlp/tupa/releases/download/v1.3.10/ucca-bilstm-1.3.10.tar.gz
tar xvzf ucca-bilstm-1.3.10.tar.gz
```
  5. Copy vocab to the service
```
cp -r vocab /server/.
```
  6. Download spacy model:
```
python -m spacy download en_core_web_md
```
  7. Install the service requirements: 
```
cd server
pip install -r requirements.txt
```
  8. Start the service
```
python parse_server.py
```
  9. Test the service
```
curl -X POST -H "Content-Type: application/json" -d '{"text": "The cat is on the table."}' http://localhost:5001/parse
```




