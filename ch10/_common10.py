"""Shared helpers for the Chapter 10 scripts.

Chapter 10 asks where the bias that survives Chapters 3 to 9 comes from, what a
sensitivity analysis would have said about it, and what the estimate means for
policy. The estimators are those of the earlier chapters; the new functions
here are the additional propensity model terms, the omitted-variable
sensitivity quantities of Cinelli and Hazlett, and Rosenbaum's bound for
matched pairs.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
for d in ("ch09", "ch07", "ch05", "ch03"):
    sys.path.insert(0, str(HERE.parent / d))
from _common9 import (cli, banner, score, nn_match, mahalanobis_match, att_weights,   # noqa: E402,F401
                      att_odds, outcome_design, outcome_fits, att_dr, make_draw, REPO, pct,
                      sandwich_se, logit_design, paired_se)

FIRST_SEED = 20260808
N_DRAWS = 40


def truth_file(datadir):
    """The generator's truth file, for scoring and for Section 10.2's experiment."""
    return pd.read_csv(Path(datadir) / "truth" / "truth_parameters.csv").set_index("person_id")


def added_terms(E, X, T=None):
    """Candidate additions to Chapter 3's propensity model.

    The first four are observed: 2016 earnings in dollars beside its log,
    age squared, education as categories, and English proficiency, which the
    analysis file carries but Chapter 3 did not use. The last two come from
    the truth file and no real analysis could include them.
    """
    ex = pd.DataFrame(index=X.index)
    inc = E["earnings_2016"]
    ex["earnings_2016_dollars"] = inc.fillna(inc.median()) / 10000
    ex["age_squared"] = (X["age"] - 40) ** 2
    ex["edu_low"] = (X["edu"] <= 1).astype(float)
    ex["edu_degree"] = (X["edu"] == 4).astype(float)
    ep = E["english_proficiency"]
    ex["english_not_well"] = (ep == "Not well").astype(float)
    ex["english_missing"] = ep.isna().astype(float)
    mo = pd.get_dummies(E["mutual_obligation_status"].fillna("Missing"), prefix="mo",
                        drop_first=True, dtype=float)
    ex = pd.concat([ex, mo.set_index(ex.index)], axis=1)
    if T is not None:
        ex["employability"] = T["u_employability"].values
        ex["shock"] = T["earnings_shock_2016"].values
    return ex


FORM = ["earnings_2016_dollars", "age_squared"]
OBSERVED = FORM + ["edu_low", "edu_degree", "english_not_well", "english_missing"]
SPECS = {                                       # Table 10.1, in order
    "Chapter 3's score": [],
    "+ 2016 earnings in dollars and age squared": FORM,
    "+ education as categories and English proficiency": OBSERVED,
    "+ the pre-programme earnings shock (truth file)": OBSERVED + ["shock"],
    "+ employability (truth file)": OBSERVED + ["employability"],
    "Employability alone (truth file)": ["employability"],
    "+ mutual obligation status": OBSERVED + ["MO"],
}


def fit_logit(M, D):
    """Chapter 3's logistic model on the columns of M."""
    from sklearn.linear_model import LogisticRegression
    Z = (M - M.mean()) / M.std().replace(0, 1)
    m = LogisticRegression(max_iter=5000, C=1e6).fit(Z, D)
    p = m.predict_proba(Z)[:, 1]
    return p, float(np.sum(D * np.log(p) + (1 - D) * np.log(1 - p)))


def likelihood_ratio(X, D, extra):
    """Likelihood-ratio test of adding `extra` to the propensity model. Fragment 10.1."""
    from scipy.stats import chi2
    _, ll0 = fit_logit(X, D)
    _, ll1 = fit_logit(pd.concat([X, extra], axis=1), D)
    lr = 2 * (ll1 - ll0)
    return lr, float(chi2.sf(lr, extra.shape[1]))


# ------------------------------------------------------ Section 10.3.1

def ols(y, V):
    Vi = np.c_[np.ones(len(y)), V]
    b, *_ = np.linalg.lstsq(Vi, y, rcond=None)
    e = y - Vi @ b
    return b, e, Vi


def partial_r2(y, base, z):
    """Share of the residual variance of y, given `base`, that z explains."""
    _, e0, _ = ols(y, base)
    _, e1, _ = ols(y, np.c_[base, z])
    return float(1 - (e1 @ e1) / (e0 @ e0))


def regression_sensitivity(y, D, Q):
    """Cinelli and Hazlett's quantities for the regression of y on D and Q. Fragment 10.2."""
    V = np.c_[D, Q]
    b, e, Vi = ols(y, V)
    df = len(y) - Vi.shape[1]
    se = float(np.sqrt(e @ e / df * np.linalg.pinv(Vi.T @ Vi)[1, 1]))
    t = b[1] / se
    f = t / np.sqrt(df)
    rv = lambda q: 0.5 * (np.sqrt((q * f) ** 4 + 4 * (q * f) ** 2) - (q * f) ** 2)   # noqa: E731
    return dict(est=float(b[1]), se=se, df=df, r2_yd=float(t ** 2 / (t ** 2 + df)),
                rv=float(rv(1.0)), rv_q=rv)


def adjusted(est, se, df, r2dz, r2yz):
    """The estimate after removing a confounder with the given partial R-squareds."""
    return est - se * np.sqrt(df) * np.sqrt(r2yz * r2dz / (1 - r2dz))


def confounder_strength(y, D, Q, z):
    """Partial R-squareds of z with treatment (given Q) and outcome (given D and Q)."""
    return partial_r2(D.astype(float), Q, z), partial_r2(y, np.c_[D, Q], z)


def benchmark(y, D, Q, cols, name):
    """Strength of an observed covariate, measured by leaving it out of Q."""
    j = cols.index(name)
    return confounder_strength(y, D, np.delete(Q, j, axis=1), Q[:, j])


# ------------------------------------------------------ Section 10.3.2

def rosenbaum_gamma(d, tau0=0.0, alpha=0.05):
    """Largest hidden bias at which the signed-rank test still rejects effect <= tau0. Fragment 10.3."""
    from scipy.stats import rankdata, norm
    x = d - tau0
    x = x[x != 0]
    r = rankdata(np.abs(x))
    T = r[x > 0].sum()

    def p_upper(G):
        p = G / (1 + G)
        return 1 - norm.cdf((T - p * r.sum()) / np.sqrt(p * (1 - p) * (r ** 2).sum()))
    if p_upper(1.0) > alpha:
        return 1.0
    lo, hi = 1.0, 20.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if p_upper(mid) <= alpha else (lo, mid)
    return lo


def within_pair_odds(logit, mt, mc):
    """How much two matched persons' odds of treatment actually differ."""
    return np.exp(np.abs(logit[mt] - logit[mc]))
