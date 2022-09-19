from tuw_nlp.common.eval import get_cat_stats, print_cat_stats


def test_eval():
    golds = [[1], [1, "foo"], [1], [1, "foo"], []]
    preds = [["foo"], [1, "foo"], [], [1], []]
    cat_stats = get_cat_stats(preds, golds)
    assert cat_stats[1]['FN'] == 2
    assert cat_stats['foo']['FP'] == 1
    print_cat_stats(cat_stats, tablefmt='latex_booktabs', floatfmt='.1%')
    print_cat_stats(cat_stats)
