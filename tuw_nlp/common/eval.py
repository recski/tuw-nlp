
def print_cat_stats(cat_stats, max_n=None, out_stream=None):
    cat_stats = count_p_r_f(cat_stats)
    cats_sorted = sorted(
        cat_stats.keys(), key=lambda k: -sum(cat_stats[k].values()))

    for cat in cats_sorted:
        s = cat_stats[cat]
        out_str = f"{cat:<50}\t{s['gold']:>4}\t{s['pred']:>4}\t{s['P']:>6.2%}\t{s['R']:>6.2%}\t{s['F']:>6.2%}"  # noqa
        if out_stream is None:
            print(out_str)
        else:
            out_stream.write(out_str)


def count_p_r_f(cat_stats):
    for cat, s in cat_stats.items():
        s['pred'] = s['TP'] + s['FP']
        s['gold'] = s['TP'] + s['FN']
        s['P'] = s['TP'] / s['pred'] if s['pred'] > 0 else 1.0
        s['R'] = s['TP'] / s['gold'] if s['gold'] > 0 else 1.0
        s['F'] = (
            0.0 if s['P'] + s['R'] == 0
            else (2 * s['P'] * s['R']) / (s['P'] + s['R']))

    return cat_stats
