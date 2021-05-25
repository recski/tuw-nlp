import argparse
import logging

from tqdm import tqdm

from tuw_nlp.common.eval import print_cat_stats
from tuw_nlp.graph.lexical import LexGraphs
from tuw_nlp.graph.utils import graph_to_pn
from tuw_nlp.grammar.text_to_4lang import TextTo4lang
from tuw_nlp.ml.rule_learner import RuleLearner
from tuw_nlp.text.preprocessor import Preprocessor


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-t", "--train-file", default=None, type=str)
    parser.add_argument("-v", "--valid-file", default=None, type=str)
    parser.add_argument("-cd", "--cache-dir", default=None, type=str)
    parser.add_argument("-cn", "--nlp-cache", default=None, type=str)
    parser.add_argument("-l", "--lang", default=None, type=str)
    parser.add_argument("-p", "--preprocessor", default=None, type=str)
    parser.add_argument("-i", "--inverse", action='store_true')
    return parser.parse_args()


def gen_events(stream, tfl, lexgraphs, preproc, inverse=False):
    for i, line in tqdm(enumerate(stream)):
        try:
            text, label = line.strip().split('\t')
            text = preproc(text)
        except ValueError:
            print(f'error on line {i}: {line}')
            yield None, None
            continue
        label = eval(label)
        assert label in (0, 1, True, False)
        label = bool(label)
        label = not label if inverse else label
        features = []
        try:
            for fl in tfl(text):
                features += [
                    sg_tuple
                    for sg_tuple, sg in lexgraphs.gen_lex_subgraphs(
                        fl, 2)]
        except (IndexError, TypeError):
            print(f'tfl error on line {i}: {text}')
            yield None, None
            continue
        yield features, bool(label)


def main():
    logging.basicConfig(
        format="%(asctime)s : " +
        "%(module)s (%(lineno)s) - %(levelname)s - %(message)s")
    logging.getLogger().setLevel(logging.WARNING)
    args = get_args()

    lexgraphs = LexGraphs()
    rl = RuleLearner(args)
    preproc = Preprocessor(args.preprocessor)
    with TextTo4lang(
            lang=args.lang, nlp_cache=args.nlp_cache,
            cache_dir=args.cache_dir) as tfl:
        with open(args.train_file) as f:
            for features, label in gen_events(
                    f, tfl, lexgraphs, preproc, inverse=args.inverse):
                if features is None:
                    continue
                rl.add_train_event(features, label)

        with open(args.valid_file) as f:
            for features, label in gen_events(
                    f, tfl, lexgraphs, preproc, inverse=args.inverse):
                if features is None:
                    continue
                rl.add_valid_event(features, label)

    # for n in range(20, 100, 10):
    # for n in (50,):
    # rules_sorted = rl.dumb_choice(fp_weight=100, min_freq=5)
    # rules_sorted = rl.dumb_choice(fp_weight=1, min_freq=5)
    # rules_sorted = rl.dumb_choice(fp_weight=1)

    rl.cutoff(5)
    rules_sorted = rl.logreg_choice()

    # rule_names = rl.get_rule_names(rules_sorted)
    with open('rules.txt', 'w') as f:
        for rule in rules_sorted[:1000]:
            rule_name = graph_to_pn(lexgraphs.from_tuple(
                rl.features.get_word(rule)))
            train_matches = rl.match(set([rule]), rl.train_events)
            valid_matches = rl.match(set([rule]), rl.valid_events)
            train_stats = {
                m_type: len(samples)
                for m_type, samples in train_matches.items()}
            valid_stats = {
                m_type: len(samples)
                for m_type, samples in valid_matches.items()}
            print_cat_stats({rule_name: train_stats}, out_stream=f)
            f.write('\t')
            print_cat_stats({rule_name: valid_stats}, out_stream=f)
            f.write('\n')

        # f.write('\n'.join(
        #     graph_to_pn(lexgraphs.from_tuple(t)) for t in rule_names))

    # for n in range(500, 2000, 100):
    # for n in (10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000):
    for n in (1, 3, 5, 10, 20, 30, 40, 50, 100, 200, 500, 1000, 2000, 5000):
        rules = rules_sorted[:n]
        print(n)
        rl.eval_rules(rules)


if __name__ == "__main__":
    main()
