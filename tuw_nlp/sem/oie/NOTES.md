### Intro

We perform a qualitative study of recent approaches to semantic parsing and
representation. The task of Open Information Extraction (OIE) is used as a proxy for
evaluating the expressivity of ... formalisms. Rule-based OIE systems for performing the
OIE task directly on semantic graphs are implemented for each graph type, their recall
is measured on several recent OIE datasets, while their precision is evaluated by
manual analysis. Our main contribution is the discussion of the strengths and weaknesses
of each rule-based system and the potential of each graph formalism as an intermediate
model of symbolic natural language understanding.


### TODOs:

- should generate greedily, go for very good recall across datasets, and control for precision manually
- MinIE is an existing rule based system over dependencies (Stanford, not UD), it is
  configurable, should try it with the greediest settings
- should probably still do an UD-based baseline
- must-have formalisms: Semantic Hypergraphs, UCCA, AMR
- UD
  - args containing APPOS should have three versions, e.g. "Tokyo, officially Tokyo
    Metropolis", "Tokyo", and "(officially) Tokyo metropolis" + APPOS needs its own pattern


### Problems:

- when does an NP entail a triplet?
TO 3	It is the seat of the Emperor of Japan and the Japanese government.
[has]	Japan	[an] Emperor
[has]	[Japan]	[a] government


### Evaluation

- Many scoring schemes, WiRE57, OIE2016, CaRB each come with their own, most recent papers also
  use the WiRE and OIE2016 scoring schemes on CaRB. It seems that the OIE2016 has
  known problems, and CaRB is meant to be an improvement over WiRE. The CaRB paper has
  details.

### Datasets

- WiRE57, 57 sentences, Wikipedia, \citep{Lechelle:2019},
  https://aclanthology.org/W19-4002/
- OPIEC, Wikipedia-based, 340M triples extracted by MinIE \citep{Gashteovski:2019}, https://openreview.net/forum?id=HJxeGb5pTm https://www.uni-mannheim.de/dws/research/resources/opiec/
- LSOIE, wiki+sci, 24K+48K sens, 57K+98K triples, \citep{Solawetz:2021}, https://github.com/Jacobsolawetz/large-scale-oie
- CaRB  crowdsourced, dev+test, 641+641 sens, 2548+2714 triplets \citep{Bhardwaj:2019} https://aclanthology.org/D19-1651/ https://github.com/dair-iitd/CaRB

### Systems

- MinIE, rule-based, SOTA on WiRe, \citep{Gashteovski:2017}, https://aclanthology.org/D17-1278/ https://www.uni-mannheim.de/dws/research/resources/minie/
- SMiLe-OIE (neural), "SOTA" on LSOIE, \citep{Dong:2022}:  https://aclanthology.org/2022.emnlp-main.272/
- OpenIE6, BERT-based sequence labeling, another SOTA on WiRE and CaRB,
  \citep{Kolluru:2020}: https://aclanthology.org/2020.emnlp-main.306/
- DeepStruct, SOTA on OIE2016 and others, but no WiRE or LSOIE \citep{Wang:2022} https://aclanthology.org/2022.findings-acl.67/
- DetIE, new neural SOTA on CaRB \citep{Vasilkovsky:2022} https://ojs.aaai.org/index.php/AAAI/article/download/21393/version/19680/21142
- A Survey on Neural Open Information Extraction, \citep{Zhou:2022}, https://www.ijcai.org/proceedings/2022/0793.pdf
### Notes

MinIE (the best by far on WiRE57) explicitly deals with negation and modality
(consider "Pinocchio believes that the hero Superman was not actually born on beautiful
Krypton.")

Evaluating openIE requires some assumption about what relations are relevant. Consider
the sentence "Tokyo is the seat of the Emperor of Japan and the Japanese government.".
Whether a relation to be extracted is is(Tokyo, seat, of ...) or is_the_seat_of(Tokyo,
...) and whether the relations has(Japan, Emperor) and has(Japan, government) should be
inferred cannot be decided without regard to potential applications. Ideally, a system
should be configurable.
For our purposes of evaluating the expressivity of semantic representations we shall
attempt to build models that greedily generate every triplet that may be a relevant fact
under some conditions.
In doing so we knowingly ignore pragmatic considerations such as the argument of
Fader et al. (2011) that
the triplet made(Faust, a deal with the Devil)
extracted from the sentence \textit{Faust made a deal with the Devil} by the ClauseIE system
is uninformative, especially compared with the alternative made_a_deal_with(Faust,
the Devil). 

When evaluating such a system against ground truth triplets, such
an approach should achieve very high recall, but cannot be expected to have good
precision, since every annotated dataset is limited to triplets that its creators
considered relevant. For example, the above sentence in WiRE57 is annotated with the
triplet is_the_seat_of(Tokyo, Emperor of Japan) but not with is(Tokyo, seat, of the
Emperor of Japan). Therefore we shall use the WiRE57 dataset to evaluate the recall of
our method only, and for measuring precision we shall rely on our own manual annotation
of the triplets output by our system.


simple UD baseline's performance on WiRE

2023.02.23 (after fixing GraphFormulaMatcher vs. GraphFormulaPatternMatcher bug):

System sym prec/rec/f1: 44.1% 7.2% 0.124

System sym prec/rec of matches only (non-matches): 71% 86% (29)

1 were exactly correct, out of 47 predicted / the reference 343.

Exact-match prec/rec/f1: 2.1% 0.3% 0.005

