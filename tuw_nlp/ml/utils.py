import numpy as np


def get_x_y(events, feat_vocab):
    X = np.zeros((len(events), len(feat_vocab)))
    y = np.zeros(len(events))
    for i, event in enumerate(events):
        for feat in event[0]:
            X[i][feat] = 1

        if event[1]:
            y[i] = 1

    return X, y
