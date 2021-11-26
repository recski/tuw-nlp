import os
import re
from collections import defaultdict
from nltk.corpus import stopwords as nltk_stopwords


class Dictionary():
    def __init__(self, lang):
        self.lexicon = defaultdict(list)
        self.lang_map = {}
        base_fn = os.path.dirname(os.path.abspath(__file__))
        langnames_fn = os.path.join(base_fn, "langnames")

        self.lang = lang

        definitions_base_fn = os.path.join(os.path.expanduser(
            "~/tuw_nlp_resources"), "definitions", lang.split("_")[0])

        definitions_fn = None
        if os.path.isfile(definitions_base_fn):
            definitions_fn = definitions_base_fn

        assert definitions_fn, 'Definition dictionaries are not downloaded, for setup please use tuw_nlp.download_definitions(), otherwise you will not be able to use expand functionalities'

        with open(langnames_fn, "r", encoding="utf8") as f:
            for line in f:
                line = line.split("\t")
                self.lang_map[line[0]] = line[1].strip("\n")

        self.stopwords = set(nltk_stopwords.words(self.lang_map[lang]))
        self.__init_lexicons(definitions_fn)

    def __init_lexicons(self, definitions_fn):
        with open(definitions_fn, "r", encoding="utf8") as f:
            for line in f:
                line = line.split("\t")
                if len(line[2].strip().strip("\n")) > 5:
                    word = line[0].strip()

                    defi = line[2].strip().strip("\n")
                    defi = self.parse_definition(defi)
                    if defi.strip() != word:
                        def_splitted = defi.strip().split(";")
                        for def_split in def_splitted:
                            if def_split not in self.lexicon[word]:
                                self.lexicon[word].append(def_split)

    def parse_definition(self, defi):
        defi = re.sub(re.escape("#"), " ",  defi).strip()

        defi = re.sub(r"^A type of", "",  defi)
        defi = re.sub(r"^Something that", "",  defi)
        defi = re.sub(r"^Relating to", "",  defi)
        defi = re.sub(r"^Someone who", "",  defi)
        defi = re.sub(r"^Of or", "",  defi)
        defi = re.sub(r"^Any of", "",  defi)
        defi = re.sub(r"^The act of", "",  defi)
        defi = re.sub(r"^A group of", "",  defi)
        defi = re.sub(r"^The part of", "",  defi)
        defi = re.sub(r"^One of the", "",  defi)
        defi = re.sub(r"^Used to", "",  defi)
        defi = re.sub(r"^An attempt to", "",  defi)

        defi = re.sub(r"^intransitive", "",  defi)
        defi = re.sub(r"^ditransitive", "",  defi)
        defi = re.sub(r"^ambitransitive", "",  defi)
        defi = re.sub(r"^transitive", "",  defi)
        defi = re.sub(r"^uncountable", "",  defi)
        defi = re.sub(r"^countable", "",  defi)
        defi = re.sub(r"^pulative ", "",  defi)
        defi = re.sub(r"^\. ", "",  defi)
        defi_words = defi.split(" ")
        first_words = defi_words[0].split(',')
        if len(first_words) > 1 and re.sub("\'s", "", first_words[0].lower()) == \
                re.sub("\'s", "", first_words[1].lower()):
            defi = " ".join([first_words[1]] + defi_words[1:])
        return defi

    def get_definition(self, word):
        return self.lexicon[word][0] if self.lexicon[word] else None
