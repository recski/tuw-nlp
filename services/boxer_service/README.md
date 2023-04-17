# Boxer service

We provide a docker service for parsing Discourse Representation Structures (DRS). The service is built on the [Transparent Semantic Parsing with Universal Dependencies Using Graph Transformations](https://aclanthology.org/2022.coling-1.367/) paper and on the [ud-boxer](https://github.com/WPoelman/ud-boxer) github repository.

Our fork can be found at: https://github.com/adaamko/ud-boxer

The docker service can be started with __docker-compose__:
    
```
docker-compose up
```

The service is available at: http://localhost:5002/parse

Then you can make a post request to parse a text into DRG (Discourse Representation Graph):
        
```
curl -X POST -H "Content-Type: application/json" -d '{"text": "The cat is on the table."}' http://localhost:5002/parse
```

The response will be a JSON object with the parsed networkx graph.


You can also manually start the service if you don't prefer to use docker:

  1. Go to our fork and clone it: https://github.com/adaamko/ud-boxer
  2. Follow the instructions to install the package and the GREW parser
  3. With this environment, install flask: pip install flask
  4. Start the service: python service.py
  5. Test the service
   
```
curl -X POST -H "Content-Type: application/json" -d '{"text": "The cat is on the table."}' http://localhost:5002/parse
```




