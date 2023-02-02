import sys
from collections import Counter, defaultdict

from tabulate import tabulate


def avg(seq):
    if len(seq) == 0:
        return 0
    return sum(seq) / len(seq)


def print_cat_stats(
    cat_stats,
    max_n=None,
    out_stream=sys.stdout,
    print_avgs=False,
    tablefmt="github",
    # floatfmt=".2%",
    floatfmt=("s", "d", "d", ".2%", ".2%", ".2%"),
    linesep="\n",  # for backward compatibility, not used
):
    table = []
    cat_stats = count_p_r_f(cat_stats)

    if print_avgs:
        cat_stats["macro_avg"] = {
            metric: avg([s[metric] for s in cat_stats.values()])
            for metric in ("P", "R", "F")
        }
        cat_stats["macro_avg"].update(
            {"gold": cat_stats["total"]["gold"], "pred": cat_stats["total"]["pred"]}
        )

    cats_sorted = sorted(
        cat_stats.keys(), key=lambda k: (-cat_stats[k]["gold"], str(k))
    )

    for cat in cats_sorted:
        s = cat_stats[cat]
        table.append([cat, s["gold"], s["pred"], s["P"], s["R"], s["F"]])

    out_stream.write(
        tabulate(
            table,
            headers=["label", "gold", "predicted", "precision", "recall", "F1"],
            tablefmt=tablefmt,
            floatfmt=floatfmt,
        )
    )
    out_stream.write("\n")


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


def get_cat_stats(preds, golds, labels_to_keep=None, add_missing_labels=False):
    assert not (add_missing_labels and labels_to_keep is None)
    stats = defaultdict(Counter)
    for pred, gold in zip(preds, golds):
        p = set(pred)
        g = set(gold)
        _add_to_stat(stats, "TP", g & p, labels_to_keep)
        _add_to_stat(stats, "FN", g - p, labels_to_keep)
        _add_to_stat(stats, "FP", p - g, labels_to_keep)
    labels = labels_to_keep if add_missing_labels else stats.keys()
    stats["total"] = {
        stat: sum(stats[label][stat] for label in labels) for stat in ("TP", "FN", "FP")
    }
    return stats


def _add_to_stat(stats, stat_type, relevant_label_set, labels_to_keep):
    for label in relevant_label_set:
        if labels_to_keep is None or label in labels_to_keep:
            stats[label][stat_type] += 1


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
