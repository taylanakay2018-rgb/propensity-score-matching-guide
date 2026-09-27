"""Shared helpers for the Chapter 7 scripts.

Chapter 7 works from the logistic score Chapter 3 fitted and the trimming rule
Chapter 4 recommended, as Chapters 5 and 6 did, and adds the estimators that
stratify on the score or model the outcome as a function of it. Every
estimator here is written out in a few lines, so that a reader can see exactly
what is being computed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ch06"))
from _common6 import (cli, banner, score, trimming_rules, nn_match,        # noqa: E402,F401
                      mahalanobis_match, matched_att, REPO, TRIM_RULE,
                      ate_weights, att_weights, ate_normalised, att_odds, kish,
                      outcome_design, outcome_fits, att_dr, pct)

KS = [2, 5, 10, 20, 50, 100]          # the numbers of strata Table 7.3 compares


# ------------------------------------------------------------ forming strata

def strata(ps, D, K, on="all"):
    """Stratum of each person: K groups of equal size on the score.

    on="all" cuts at quantiles of everyone's score, which is the usual choice;
    on="treated" cuts at quantiles of the treated persons' scores only.
    """
    base = ps if on == "all" else ps[D == 1]
    q = np.unique(np.quantile(base, np.linspace(0, 1, K + 1)))
    q[0], q[-1] = -np.inf, np.inf
    return np.searchsorted(q, ps, side="right") - 1


def subclass(ps, D, y, K, estimand="ATT", on="all", Q=None):
    """The subclassification estimate. See Fragment 7.1.

    Within each stratum, the difference in mean outcomes (or, given Q, the
    coefficient on treatment in a regression on Q; see Fragment 7.3). The
    stratum differences are averaged with weights equal to the stratum's
    treated count for the ATT, or its total count for the ATE. Returns the
    estimate, its naive standard error, and the number of strata lacking
    either group, which are dropped.
    """
    from sklearn.linear_model import LinearRegression
    s = strata(ps, D, K, on)
    w, d, v, dropped = [], [], [], 0
    for k in np.unique(s):
        m = s == k
        t, c = m & (D == 1), m & (D == 0)
        if t.sum() == 0 or c.sum() == 0:
            dropped += 1
            continue
        if Q is None:
            d.append(y[t].mean() - y[c].mean())
        else:
            d.append(LinearRegression().fit(np.c_[D[m], Q[m]], y[m]).coef_[0])
        v.append((y[t].var(ddof=1) / t.sum() if t.sum() > 1 else 0.0)
                 + (y[c].var(ddof=1) / c.sum() if c.sum() > 1 else 0.0))
        w.append(t.sum() if estimand == "ATT" else m.sum())
    w = np.array(w, float) / np.sum(w)
    return float(w @ np.array(d)), float(np.sqrt(w ** 2 @ np.array(v))), dropped


def stratum_weights(ps, D, K, estimand="ATT"):
    """The weights that make a weighted mean reproduce subclassification.

    See Fragment 7.2. For the ATT, every treated person counts once and each
    control counts (treated in the stratum) / (controls in the stratum). For
    the ATE, each person counts (persons in the stratum) / (persons in their
    group in the stratum), so both groups are weighted up to the stratum's
    size. These are marginal mean weights through stratification.
    """
    s = strata(ps, D, K)
    w = np.zeros(len(D))
    for k in np.unique(s):
        m = s == k
        n1, n0 = (m & (D == 1)).sum(), (m & (D == 0)).sum()
        if n1 == 0 or n0 == 0:
            continue
        if estimand == "ATT":
            w[m & (D == 1)] = 1.0
            w[m & (D == 0)] = n1 / n0
        else:
            w[m & (D == 1)] = m.sum() / n1
            w[m & (D == 0)] = m.sum() / n0
    return w


def stratified_smd(X, ps, D, K, estimand="ATT"):
    """Standardised mean difference of each covariate after stratification.

    The within-stratum differences in means, averaged with the estimand's
    stratum weights and divided by the covariate's standard deviation in the
    whole sample. Chapter 8 develops balance diagnostics properly.
    """
    s = strata(ps, D, K)
    V = X.values.astype(float)
    sd = np.where(V.std(0) > 0, V.std(0), 1.0)
    tot, wsum = np.zeros(V.shape[1]), 0.0
    for k in np.unique(s):
        m = s == k
        t, c = m & (D == 1), m & (D == 0)
        if t.sum() == 0 or c.sum() == 0:
            continue
        wk = t.sum() if estimand == "ATT" else m.sum()
        tot += wk * (V[t].mean(0) - V[c].mean(0))
        wsum += wk
    return tot / wsum / sd


# ---------------------------------------------------- models on the score

def regression_on_score(ps, D, y):
    """The coefficient on treatment in y ~ D + ps. Section 7.7's box."""
    from sklearn.linear_model import LinearRegression
    return LinearRegression().fit(np.c_[D, ps], y).coef_[0]


def overlap_truth(ps, tau):
    """The effect averaged with weights ps(1 - ps): the overlap population."""
    h = ps * (1 - ps)
    return float((h * tau).sum() / h.sum())


def spline_basis(ps, knots="quantile", n_knots=10):
    """A cubic spline basis in the logit of the score. See Fragment 7.4.

    knots="quantile" places the knots at quantiles of the score, so that
    every interval between knots contains data. knots="uniform", the library
    default, spaces them evenly across the score's range; Section 7.9's Trap
    box shows what that does.
    """
    from sklearn.preprocessing import SplineTransformer
    lp = np.log(ps / (1 - ps)).reshape(-1, 1)
    return SplineTransformer(n_knots=n_knots, degree=3, knots=knots).fit_transform(lp)


def spline_on_score(ps, D, y, Q=None, knots="quantile"):
    """Outcome models on a spline of the score, one per condition.

    Each person's two potential outcomes are predicted from the model for each
    condition; with Q, the covariates enter beside the spline. Returns the
    ATE and ATT estimates.
    """
    from sklearn.linear_model import LinearRegression
    B = spline_basis(ps, knots)
    V = B if Q is None else np.c_[B, Q]
    m1 = LinearRegression().fit(V[D == 1], y[D == 1]).predict(V)
    m0 = LinearRegression().fit(V[D == 0], y[D == 0]).predict(V)
    return float((m1 - m0).mean()), float((y[D == 1] - m0[D == 1]).mean())


def make_draw(seed, tmp):
    """Generate one draw and build its analysis file, as Chapters 5 and 6 do."""
    import subprocess
    out = tmp / f"d{seed}"
    subprocess.run([sys.executable, str(REPO / "make_data.py"), "--seed", str(seed),
                    "--n", "50000", "--outdir", str(out), "--quiet"], check=True)
    for s in ("ch02/02_05_link_modules.py", "ch02/02_06_reshape_panel.py"):
        subprocess.run([sys.executable, str(REPO / s), "--datadir", str(out)],
                       check=True, capture_output=True)
    return out
