# tuw-nlp

## Modules

### text 

- from `brise-nlp/common/nlp`: everything
- from `surface_realization/utils`: tsv, conll tools -> text.corpus

### eval ?

- from `brise-nlp/common/utils`: eval tools (to `xeval.py` ?)


### grammar

- from `brise_nlp/grammar`:
    - from lexicon: "as is" (?)
    - from uddl: integrate functions to `irtg.py`


- from `brise-nlp/common/utils`: some graph tools
- from `surface_realization`:
    - from `utils`:
        - `sanitize_...` (to alto module)
        - `irtg/alto corpus writers/readers (to `irtg.py`)
    - from `converter`: ?? (Adam, do we need anything?)
    - from `surface_realization`: alto execution


### graph

- from `surface_realization`:
    - from `utils`:
        - `get_rules` (generic graph function to get subgraphs)
        - `get_isi_sgraph` (to sgraph writer method)
- 

