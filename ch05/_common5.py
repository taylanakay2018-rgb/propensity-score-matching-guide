"""Shared helpers for the Chapter 5 scripts.

Chapter 5 works from the score Chapter 3 fitted, which these helpers reproduce
rather than reading a saved copy. Chapter 4's trimming rule is available here
and Script 5.1 applies it, but the chapter's comparisons match on the untrimmed
eligible population; Section 5.4 explains why, and Script 5.3 checks that
trimming changes none of its findings. Every matching procedure in the chapter
is built from the four primitives below.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ch04"))
from _common4 import (cli, banner, score, trimming_rules, REPO)          # noqa: E402


def linear_predictor(ps: np.ndarray) -> np.ndarray:
    """Matching is done on the log odds, not the probability. See Section 5.3.1."""
    q = np.clip(ps, 1e-6, 1 - 1e-6)
    return np.log(q / (1 - q))


def nn_match(ps, D, caliper=0.1, replace=False, ratio=1):
    """Greedy nearest neighbour, hardest to match first. See Fragment 5.1."""
    from sklearn.neighbors import NearestNeighbors
    lp = linear_predictor(ps)
    cal = caliper * lp.std()
    t = np.where(D == 1)[0]
    c = np.where(D == 0)[0]
    t = t[np.argsort(-ps[t])]                      # descending propensity
    pairs = []
    if replace:
        nn = NearestNeighbors(n_neighbors=ratio).fit(lp[c].reshape(-1, 1))
        d, i = nn.kneighbors(lp[t].reshape(-1, 1))
        for k, ti in enumerate(t):
            for r in range(ratio):
                if d[k, r] <= cal:
                    pairs.append((ti, c[i[k, r]]))
    else:
        taken = np.zeros(len(c), bool)
        for ti in t:
            dist = np.abs(lp[c] - lp[ti])
            dist[taken] = np.inf
            for _ in range(ratio):
                j = int(np.argmin(dist))
                if dist[j] > cal:
                    break
                pairs.append((ti, c[j]))
                taken[j] = True
                dist[j] = np.inf
    if not pairs:
        return np.array([], int), np.array([], int)
    P = np.array(pairs)
    return P[:, 0], P[:, 1]


# The four covariates carrying most of the confounding, per Chapter 2.
MAHA_COLS = ["log_inc_2016", "fn_2016", "age", "edu"]


def mahalanobis_match(X, D, ps, caliper=0.1, cols=None):
    """Mahalanobis distance on a few covariates, inside a propensity caliper.

    Section 5.6: this is the decision that moves the estimate, and the choice
    of which covariates enter the distance is a real one. Pass cols=list(X.columns)
    to use all eighteen; across Table 5.4's twelve draws that did better than
    the four, which carry much of the confounding but not all of it.
    """
    cols = cols or MAHA_COLS
    Z = ((X[cols] - X[cols].mean()) / X[cols].std()).values
    lp = linear_predictor(ps)
    cal = caliper * lp.std()
    t = np.where(D == 1)[0]
    c = np.where(D == 0)[0]
    S = np.linalg.pinv(np.cov(Z[c].T))
    taken = np.zeros(len(c), bool)
    pairs = []
    for ti in t[np.argsort(-ps[t])]:
        ok = (np.abs(lp[c] - lp[ti]) <= cal) & (~taken)
        if not ok.any():
            continue
        idx = np.where(ok)[0]
        dv = Z[c[idx]] - Z[ti]
        j = idx[int(np.argmin(np.einsum("ij,jk,ik->i", dv, S, dv)))]
        pairs.append((ti, c[j]))
        taken[j] = True
    if not pairs:
        return np.array([], int), np.array([], int)
    P = np.array(pairs)
    return P[:, 0], P[:, 1]


def optimal_match(ps, D, caliper=0.1, cap_t=2500, cap_c=7500, seed=0):
    """Minimise total distance across the whole assignment. See Section 5.8.

    Capped, because the assignment problem scales badly and the full problem is
    slow enough to be inconvenient. The cap is why Table 5.6 compares optimal
    with greedy on a subproblem rather than on the whole sample.
    """
    from scipy.optimize import linear_sum_assignment
    lp = linear_predictor(ps)
    cal = caliper * lp.std()
    rng = np.random.default_rng(seed)
    t = np.where(D == 1)[0]
    c = np.where(D == 0)[0]
    if len(t) > cap_t:
        t = rng.choice(t, cap_t, replace=False)
    if len(c) > cap_c:
        c = rng.choice(c, cap_c, replace=False)
    M = np.abs(lp[t][:, None] - lp[c][None, :])
    M[M > cal] = 1e6
    ri, ci = linear_sum_assignment(M)
    ok = M[ri, ci] < 1e6
    return t[ri[ok]], c[ci[ok]], t, c


def matched_att(mt, mc, y, tau):
    """Bias against the true ATT for the treated persons actually matched."""
    if len(mt) == 0:
        return np.nan, np.nan, np.nan
    d = y[mt] - y[mc]
    truth = tau[mt].mean()
    return 100 * (d.mean() - truth) / truth, d.mean(), d.std(ddof=1) / np.sqrt(len(d))


def smd(v, a, b):
    s = np.sqrt((v[a].var() + v[b].var()) / 2)
    return float((v[a].mean() - v[b].mean()) / s) if s > 0 else 0.0
