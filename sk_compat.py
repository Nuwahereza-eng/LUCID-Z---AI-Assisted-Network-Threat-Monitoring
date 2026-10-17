"""Optional scikit-learn: use it when installed, else minimal NumPy equivalents.

LUCID only needs CountVectorizer (protocol-name features) and three binary
classification metrics. The fallbacks below reproduce sklearn's behaviour for
those uses, so the app runs where sklearn/scipy have no wheels (e.g. IBM Z
s390x) without compiling them from source.
"""
import re

import numpy as np


class _Matrix(np.ndarray):
    """ndarray that also answers sklearn's sparse-matrix toarray()/todense()."""

    def toarray(self):
        return np.asarray(self)

    todense = toarray


class _CountVectorizer:
    # sklearn defaults: lowercase=True, token_pattern=r"(?u)\b\w\w+\b", sorted vocabulary
    _token = re.compile(r"(?u)\b\w\w+\b")

    def __init__(self):
        self.vocabulary_ = {}

    def _tokens(self, doc):
        return self._token.findall(doc.lower())

    def fit(self, docs):
        terms = sorted({t for d in docs for t in self._tokens(d)})
        self.vocabulary_ = {t: i for i, t in enumerate(terms)}
        return self

    def transform(self, docs):
        out = np.zeros((len(docs), len(self.vocabulary_)), dtype=np.int64)
        for row, d in enumerate(docs):
            for t in self._tokens(d):
                col = self.vocabulary_.get(t)
                if col is not None:
                    out[row, col] += 1
        return out.view(_Matrix)

    def fit_transform(self, docs):
        return self.fit(docs).transform(docs)


def _accuracy_score(y_true, y_pred):
    return float(np.mean(np.asarray(y_true) == np.asarray(y_pred)))


def _confusion_matrix(y_true, y_pred, labels=(0, 1)):
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    cm = np.zeros((len(labels), len(labels)), dtype=np.int64)
    for i, a in enumerate(labels):
        for j, b in enumerate(labels):
            cm[i, j] = int(np.sum((y_true == a) & (y_pred == b)))
    return cm


def _f1_score(y_true, y_pred, zero_division=0):
    (_, fp), (fn, tp) = _confusion_matrix(np.asarray(y_true).astype(int), np.asarray(y_pred).astype(int))
    denom = 2 * tp + fp + fn
    return float(2 * tp / denom) if denom else float(zero_division)


try:
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
except ImportError:
    CountVectorizer = _CountVectorizer
    accuracy_score, f1_score, confusion_matrix = _accuracy_score, _f1_score, _confusion_matrix
