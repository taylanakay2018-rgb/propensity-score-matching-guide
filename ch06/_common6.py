"""Shared helpers for the Chapter 6 scripts.

Chapter 6 works from the score Chapter 3 fitted and the trimming rule Chapter 4
recommended, and compares what it finds with the matching of Chapter 5. These
helpers reproduce all three rather than reading saved copies, and add the
weighting estimators the chapter develops. Every estimator here is written out
in a few lines, so that a reader can see exactly what is being computed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ch05"))
from _common5 import (cli, banner, score, trimming_rules, nn_match,       # noqa: E402
                      mahalanobis_match, matched_att, REPO)

TRIM_RULE = "5  variance-minimising"          # Chapter 4's recommendation


# ---------------------------------------------------------------- the weights

def ate_weights(ps, D):
    """Inverse probability weights for the ATE. See Fragment 6.1."""
    return np.where(D == 1, 1 / ps, 1 / (1 - ps))


def stabilised_weights(ps, D):
    """The same weights multiplied by the share in each condition."""
    p = D.mean()
    return np.where(D == 1, p / ps, (1 - p) / (1 - ps))


def att_weights(ps, D):
    """Odds weights for the ATT: 1 for the treated, ps / (1 - ps) for controls."""
    return np.where(D == 1, 1.0, ps / (1 - ps))


def kish(w):
    """Effective sample size of a set of weights."""
    return w.sum() ** 2 / (w ** 2).sum()


def cap(w, mask, q):
    """Winsorise the weights in `mask` at their q-th percentile. Section 6.6."""
    w = w.copy()
    if q < 100:
        w[mask] = np.minimum(w[mask], np.percentile(w[mask], q))
    return w


# ------------------------------------------------------------ the estimators

def ate_unnormalised(ps, D, y):
    """Horvitz-Thompson: divide by n, not by the sum of the weights."""
    return np.mean(D * y / ps) - np.mean((1 - D) * y / (1 - ps))


def ate_normalised(D, y, w):
    """Weighted means within each condition. See Fragment 6.2."""
    return (np.average(y[D == 1], weights=w[D == 1])
            - np.average(y[D == 0], weights=w[D == 0]))


def att_odds(D, y, w):
    """Treated mean less the odds-weighted control mean."""
    return y[D == 1].mean() - np.average(y[D == 0], weights=w[D == 0])


def ate_se(ps, D, y):
    """The naive influence-function standard error of the normalised ATE."""
    w = ate_weights(ps, D)
    m1 = np.average(y[D == 1], weights=w[D == 1])
    m0 = np.average(y[D == 0], weights=w[D == 0])
    psi = D * (y - m1) / ps - (1 - D) * (y - m0) / (1 - ps)
    return psi.std(ddof=1) / np.sqrt(len(y))


def att_se(ps, D, y):
    """The naive influence-function standard error of the odds-weighted ATT."""
    w = att_weights(ps, D)
    m0 = np.average(y[D == 0], weights=w[D == 0])
    m1 = y[D == 1].mean()
    psi = (D * (y - m1) - (1 - D) * w * (y - m0)) / D.mean()
    return psi.std(ddof=1) / np.sqrt(len(y))


# ------------------------------------------------------ the outcome model

def outcome_design(E, X, with_occupation=True):
    """The covariates of the outcome model: the eighteen, plus occupation.

    occupation_group is the pure outcome predictor Chapter 2 identified and
    Chapter 3 held back from the propensity model. This is where it enters.
    """
    Q = X.copy()
    if with_occupation:
        occ = E["occupation_group"].fillna("None").astype(str)
        Q = pd.concat([Q, pd.get_dummies(occ, prefix="occ", drop_first=True)
                       .astype(float).set_index(Q.index)], axis=1)
    return Q


def outcome_fits(Q, D, y):
    """Linear models of the outcome, fitted separately on each condition."""
    from sklearn.linear_model import LinearRegression
    V = Q.values
    m1 = LinearRegression().fit(V[D == 1], y[D == 1]).predict(V)
    m0 = LinearRegression().fit(V[D == 0], y[D == 0]).predict(V)
    return m1, m0


def ate_dr(ps, D, y, m1, m0):
    """Augmented IPW: the regression estimate plus weighted residuals."""
    s = m1 - m0 + D * (y - m1) / ps - (1 - D) * (y - m0) / (1 - ps)
    return s.mean(), s.std(ddof=1) / np.sqrt(len(s))


def att_dr(ps, D, y, m0):
    """Doubly robust ATT: residuals from the control model, odds-weighted."""
    w = ps / (1 - ps)
    r = y - m0
    est = r[D == 1].mean() - np.average(r[D == 0], weights=w[D == 0])
    c = np.average(r[D == 0], weights=w[D == 0])
    psi = (D * (r - r[D == 1].mean()) - (1 - D) * w * (r - c)) / D.mean()
    return est, psi.std(ddof=1) / np.sqrt(len(y))


def att_regression(D, y, m0):
    """The outcome model alone: each treated person against their prediction."""
    return (y[D == 1] - m0[D == 1]).mean()


def pct(est, truth):
    return 100 * (est - truth) / truth
