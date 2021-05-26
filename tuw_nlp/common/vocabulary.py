from collections import Counter
from heapq import nlargest


class Vocabulary():
    @staticmethod
    def from_file(fn):
        with open(fn) as f:
            v = Vocabulary()
            for line in f:
                v.add(line.strip())
        return v

    def __init__(self):
        self.id_to_word = {}
        self.word_to_id = {}
        self.word_to_freq = Counter()
        self.next_id = 0

    def __contains__(self, item):
        return item in self.word_to_id

    def __len__(self):
        return self.next_id

    def to_file(self, fn):
        with open(fn, 'w') as f:
            for i in range(self.next_id):
                f.write(f"{self.id_to_word[i]}\n")

    def add(self, word, fail_if_exists=False):
        if word in self.word_to_id:
            if fail_if_exists:
                raise ValueError(
                    f'{word} already added and fail_if_exists set to True')
        else:
            self.id_to_word[self.next_id] = word
            self.word_to_id[word] = self.next_id
            self.next_id += 1

    def get_id(self, word, allow_new=False):
        if allow_new is False and word not in self.word_to_id:
            raise ValueError(
                f'{word} not in vocab and allow_new set to False')
        self.add(word)
        self.word_to_freq[word] += 1
        return self.word_to_id[word]

    def get_word(self, word_id):
        return self.id_to_word[word_id]

    def select_n_best(self, max_features):
        res_largest = [word[0] for word in self.word_to_freq.most_common(max_features)]

        relabeled_indices = {}

        for i, top in enumerate(res_largest):
            relabeled_indices[self.word_to_id[top]] = i

        return relabeled_indices, len(res_largest)

    def select_n_best_from_each_class(self, max_features, edge_to_features, up_to):
        def subsetter(c, sub):
            out = {}
            for x in sub:
                out[self.get_word(x)] = c[self.get_word(x)]
            return Counter(out)

        largest_subsets = []

        for i in range(1, up_to+1):
            subset = subsetter(self.word_to_freq, edge_to_features[i])
            most_common = [(word[0], word[1]*i) for word in subset.most_common(max_features)]
            largest_subsets += most_common
        
        largest_subsets.sort(reverse=True, key=lambda x: x[1])

        largest_subsets = [i[0] for i in largest_subsets]

        relabeled_indices = {}

        for i, top in enumerate(largest_subsets):
            relabeled_indices[self.word_to_id[top]] = i

        return relabeled_indices, len(largest_subsets)
