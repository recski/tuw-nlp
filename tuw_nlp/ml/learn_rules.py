import argparse
import logging

from tqdm import tqdm

from tuw_nlp.common.eval import print_cat_stats
from tuw_nlp.ml.featurizer import get_featurizer
from tuw_nlp.ml.rule_learner import RuleLearner


def get_args():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('method', metavar='METHOD', type=str)
    parser.add_argument("-t", "--train-file", default=None, type=str)
    parser.add_argument("-v", "--valid-file", default=None, type=str)
    parser.add_argument("-cd", "--cache-dir", default=None, type=str)
    parser.add_argument("-cn", "--nlp-cache", default=None, type=str)
    parser.add_argument("-l", "--lang", default=None, type=str)
    parser.add_argument("-p", "--preprocessor", default=None, type=str)
    parser.add_argument("-i", "--inverse", action='store_true')
    return parser.parse_args()


def read_data(stream, inverse=False):
    for i, line in enumerate(stream):
        try:
            text, label = line.strip().split('\t')
        except ValueError:
            print(f'error on line {i}: {line}')
            yield None, None
            continue
        label = eval(label)
        assert label in (0, 1, True, False)
        label = bool(label)
        label = not label if inverse else label

        yield text, label


def main():
    logging.basicConfig(
        format="%(asctime)s : " +
        "%(module)s (%(lineno)s) - %(levelname)s - %(message)s")
    logging.getLogger().setLevel(logging.WARNING)
    args = get_args()

    rl = RuleLearner(args)

    featurizer = get_featurizer(
        args.method, cache_dir=args.cache_dir, lang=args.lang,
        preprocessor=args.preprocessor)

    with open(args.train_file) as f:
        for features, label in tqdm(featurizer.gen_events(
                read_data(f, inverse=args.inverse))):
            if features is None:
                continue
            rl.add_train_event(features, label)

    logging.warning(f'# train events: {len(rl.train_events)}')

    with open(args.valid_file) as f:
        for features, label in tqdm(featurizer.gen_events(
                read_data(f, inverse=args.inverse))):
            if features is None:
                continue
            rl.add_valid_event(features, label)

    logging.warning(f'# validation events: {len(rl.valid_events)}')

    # for n in range(20, 100, 10):
    # for n in (50,):
    rules_sorted = rl.dumb_choice(fp_weight=100, min_freq=5)
    # rules_sorted = rl.dumb_choice(fp_weight=1, min_freq=5)
    # rules_sorted = rl.dumb_choice(fp_weight=1)

    # rl.cutoff(5)
    # rules_sorted = rl.logreg_choice()

    # rule_names = rl.get_rule_names(rules_sorted)
    with open('rules.txt', 'w') as f:
        for rule in rules_sorted[:1000]:
            rule_name = featurizer.get_feat_name(rl.features.get_word(rule))
            train_matches = rl.match(set([rule]), rl.train_events)
            valid_matches = rl.match(set([rule]), rl.valid_events)
            train_stats = {
                m_type: len(samples)
                for m_type, samples in train_matches.items()}
            valid_stats = {
                m_type: len(samples)
                for m_type, samples in valid_matches.items()}
            print_cat_stats({rule_name: train_stats}, out_stream=f, linesep='')
            f.write('\t')
            print_cat_stats({rule_name: valid_stats}, out_stream=f, linesep='')
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
