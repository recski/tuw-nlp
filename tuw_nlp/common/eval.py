import sys
from collections import Counter, defaultdict


def avg(seq):
    if len(seq) == 0:
        return 0
    return sum(seq) / len(seq)


def print_cat_stats(
    cat_stats, max_n=None, out_stream=sys.stdout, print_avgs=False, linesep="\n"
):
    lines = []
    cat_stats = count_p_r_f(cat_stats)
    cats_sorted = sorted(cat_stats.keys(), key=lambda k: -sum(cat_stats[k].values()))

    for cat in cats_sorted:
        s = cat_stats[cat]
        lines.append(
            f"{cat:<50}\t{s['gold']:>4}\t{s['pred']:>4}\t{s['P']:>6.2%}\t{s['R']:>6.2%}\t{s['F']:>6.2%}"
        )  # noqa

    if print_avgs:
        d = {
            metric: avg([s[metric] for s in cat_stats.values()])
            for metric in ("P", "R", "F", "gold", "pred")
        }

        cat = "macro_avg"
        lines.append(
            f"{cat:<50}\t{d['gold']:>4}\t{d['pred']:>4}\t{d['P']:>6.2%}\t{d['R']:>6.2%}\t{d['F']:>6.2%}"
        )  # noqa

    out_stream.write(linesep.join(lines) + linesep)


def count_p_r_f(cat_stats):
    for cat, s in cat_stats.items():
        s["pred"] = s["TP"] + s["FP"]
        s["gold"] = s["TP"] + s["FN"]
        s["P"] = s["TP"] / s["pred"] if s["pred"] > 0 else 1.0
        s["R"] = s["TP"] / s["gold"] if s["gold"] > 0 else 1.0
        s["F"] = (
            0.0 if s["P"] + s["R"] == 0 else (2 * s["P"] * s["R"]) / (s["P"] + s["R"])
        )

    return cat_stats


def get_cat_stats(preds, golds):
    stats = defaultdict(Counter)
    for pred, gold in zip(preds, golds):
        p = set(pred)
        g = set(gold)
        for label in p & g:
            stats[label]["TP"] += 1
        for label in g - p:
            stats[label]["FN"] += 1
        for label in p - g:
            stats[label]["FP"] += 1

    stats["total"] = {
        stat: sum(s[stat] for s in stats.values()) for stat in ("TP", "FN", "FP")
    }

    return stats


def get_stats_for_single_label(pred, gold):
    stats = Counter()
    for i, p in enumerate(pred):
        g = gold[i]
        assert p.isinstance(bool) and g.isinstance(
            bool
        ), "get_stats_for_single_label should only be used with lists of booleans"
        if g:
            if p:
                stats["TP"] += 1
            else:
                stats["FN"] += 1
        else:
            if p:
                stats["FP"] += 1
            else:
                stats["TN"] += 1

    return stats
