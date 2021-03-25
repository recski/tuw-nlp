from collections import defaultdict
from heapq import nlargest


class Vocabulary():
    def __init__(self):
        self.id_to_word = {}
        self.word_to_id = {}
        self.word_to_freq = defaultdict(int)
        self.next_id = 0

    def __len__(self):
        return self.next_id

    def add(self, word, fail_if_exists=False):
        if word in self.word_to_id:
            if fail_if_exists:
                raise ValueError(
                    f'{word} already added and fail_if_exists set to True')
        else:
            self.id_to_word[self.next_id] = word
            self.word_to_id[word] = self.next_id
            self.next_id += 1

    def get_id(self, word, allow_new=True):
        if allow_new is False and word not in self.word_to_id:
            raise ValueError(
                f'{word} not in vocab and allow_new set to False')
        self.add(word)
        self.word_to_freq[word] += 1
        return self.word_to_id[word]

    def get_word(self, word_id):
        return self.id_to_word[word_id]

    def select_n_best(self, max_features):
        res_largest = nlargest(
            max_features, self.word_to_freq, key=self.word_to_freq.get)

        relabeled_indices = {}

        for i, top in enumerate(res_largest):
            relabeled_indices[self.word_to_id[top]] = i

        return relabeled_indices, len(res_largest)
