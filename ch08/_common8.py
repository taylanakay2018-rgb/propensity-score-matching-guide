"""Shared helpers for the Chapter 8 scripts.

Every adjusted sample in this chapter, whether it came from matching,
weighting or stratification, is written the same way: a weight for each
treated person and a weight for each control, with zero for anyone the
method left out. A matched pair gives each member a weight of one, and a
control used twice gets two. Every diagnostic is then one function of those
weights, so that the same code assesses all three families of method.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ch07"))
from _common7 import (cli, banner, score, nn_match, mahalanobis_match,      # noqa: E402,F401
                      att_weights, stratum_weights, outcome_design, make_draw,
                      REPO, pct)

# Continuous and ordinal covariates, for which a variance ratio and a
# distributional comparison mean something. The rest are indicators.
CONTINUOUS = ["age", "kids", "edu", "remote", "seifa", "fn_2016", "gp",
              "log_inc_2014", "log_inc_2015", "log_inc_2016", "drop_2016"]

# Pre-programme variables in the analysis file that the propensity model of
# Chapter 3 does not use. mutual_obligation_status is the near-instrument.
HELD_OUT = ["occupation_group", "english_proficiency", "family_composition",
            "country_of_birth_group", "state", "labour_force_status_2016",
            "mutual_obligation_status"]
HELD_OUT_NUMERIC = ["pbs_scripts", "earnings_volatility"]

LABELS = {"age": "age", "kids": "dependent children", "edu": "highest education",
          "remote": "remoteness", "seifa": "SEIFA decile", "fn_2016": "fortnights on payment",
          "gp": "GP attendances", "log_inc_2014": "log earnings 2014",
          "log_inc_2015": "log earnings 2015", "log_inc_2016": "log earnings 2016",
          "drop_2016": "earnings drop 2016", "female": "female", "lts": "long-term recipient",
          "mh": "mental health item", "inc_2014_missing": "earnings 2014 missing",
          "inc_2015_missing": "earnings 2015 missing", "inc_2016_missing": "earnings 2016 missing",
          "drop_missing": "earnings drop missing"}


# ------------------------------------------------------------ the samples

def pair_weights(mt, mc, n):
    """Matched pairs as weights: each use of a person adds one."""
    wt, wc = np.zeros(n), np.zeros(n)
    np.add.at(wt, mt, 1.0)
    np.add.at(wc, mc, 1.0)
    return wt, wc


def adjusted_samples(X, D, ps, strata=(2, 5, 20, 100)):
    """The adjusted samples compared throughout the chapter, as (wt, wc)."""
    n = len(D)
    out = {"Unadjusted": ((D == 1) * 1.0, (D == 0) * 1.0)}
    out["Propensity score matching"] = pair_weights(*nn_match(ps, D, 0.1, False, 1), n)
    out["Mahalanobis matching"] = pair_weights(*mahalanobis_match(X, D, ps, 0.1), n)
    out["Odds weighting"] = ((D == 1) * 1.0, np.where(D == 0, att_weights(ps, D), 0.0))
    for K in strata:
        w = stratum_weights(ps, D, K, "ATT")
        out[f"Subclassification, {K} strata"] = (np.where(D == 1, w, 0.0),
                                                 np.where(D == 0, w, 0.0))
    return out


# ------------------------------------------------------------ diagnostics

def wmean(V, w):
    w = w / w.sum()
    return w @ V


def wvar(V, w):
    m = wmean(V, w)
    return wmean((V - m) ** 2, w)


def pooled_sd(V, D):
    """The denominator, fixed in the unadjusted sample. See Section 8.3.2."""
    sd = np.sqrt((V[D == 1].var(0) + V[D == 0].var(0)) / 2)
    return np.where(sd > 0, sd, 1.0)


def smd(V, wt, wc, sd):
    """Weighted standardised mean difference, treated less controls. Fragment 8.1."""
    return (wmean(V, wt) - wmean(V, wc)) / sd


def variance_ratio(V, wt, wc):
    """Weighted variance of the treated over that of the controls."""
    return wvar(V, wt) / wvar(V, wc)


def ks(v, wt, wc):
    """Weighted Kolmogorov-Smirnov distance: the largest gap between the two
    groups' cumulative distributions, evaluated at every observed value."""
    o = np.argsort(v, kind="stable")
    v, a, b = v[o], wt[o] / wt.sum(), wc[o] / wc.sum()
    last = np.r_[v[1:] != v[:-1], True]            # after the last of any tied values
    return float(np.abs(np.cumsum(a)[last] - np.cumsum(b)[last]).max())


def constructed_terms(X):
    """Squares of the non-binary covariates and every pairwise product.

    Computed on standardised covariates, so that a product is centred near
    zero and its standardised difference is comparable with the others.
    """
    Z = (X - X.mean()) / X.std()
    cols, V, out = list(Z.columns), Z.values, {}
    for i, a in enumerate(cols):
        if X[a].nunique() > 2:
            out[f"{a}^2"] = V[:, i] ** 2
        for j in range(i + 1, len(cols)):
            out[f"{a} x {cols[j]}"] = V[:, i] * V[:, j]
    return pd.DataFrame(out, index=X.index)


def held_out_matrix(E):
    """Indicators for each category of the held-out variables, plus the numeric ones."""
    parts = [pd.get_dummies(E[c].fillna("Missing").astype(str), prefix=c, dtype=float)
             for c in HELD_OUT]
    num = E[HELD_OUT_NUMERIC].fillna(E[HELD_OUT_NUMERIC].median())
    return pd.concat(parts + [num], axis=1)


def diagnostics(X, D, wt, wc, C=None, H=None):
    """Every covariate diagnostic of Sections 8.3 to 8.5 for one sample."""
    V = X.values.astype(float)
    s = smd(V, wt, wc, pooled_sd(V, D))
    ci = [list(X.columns).index(c) for c in CONTINUOUS]
    vr = variance_ratio(V[:, ci], wt, wc)
    k = np.array([ks(V[:, i], wt, wc) for i in ci])
    out = dict(smd=pd.Series(s, X.columns), vr=pd.Series(vr, CONTINUOUS),
               ks=pd.Series(k, CONTINUOUS))
    if C is not None:
        Cv = C.values
        out["constructed"] = pd.Series(smd(Cv, wt, wc, pooled_sd(Cv, D)), C.columns)
    if H is not None:
        Hv = H.values
        out["held_out"] = pd.Series(smd(Hv, wt, wc, pooled_sd(Hv, D)), H.columns)
    return out


def summary(d):
    """The one-line summary of a sample's diagnostics that Tables 8.2 and 8.4 report."""
    a = d["smd"].abs()
    lv = np.abs(np.log(d["vr"]))
    r = dict(smd_max=a.max(), smd_over_01=int((a > 0.1).sum()), smd_over_005=int((a > 0.05).sum()),
             smd_worst=a.idxmax(), vr_out=int(((d["vr"] < 0.8) | (d["vr"] > 1.25)).sum()),
             vr_extreme=float(d["vr"].iloc[int(lv.values.argmax())]), ks_max=d["ks"].max())
    if "constructed" in d:
        c = d["constructed"].abs()
        r.update(con_max=c.max(), con_over_01=int((c > 0.1).sum()), con_n=len(c))
    if "held_out" in d:
        h = d["held_out"].abs()
        mo = h.index.str.startswith("mutual_obligation")
        r.update(held_max=h[~mo].max(), held_worst=h[~mo].idxmax(), near_instrument=h[mo].max())
    return r


# ------------------------------------------------------------ Section 8.8

def prognostic_score(Q, D, y, seed=0):
    """Predicted outcome without treatment, from the controls only. Fragment 8.3.

    A gradient boosting model of the outcome is fitted to the controls and
    used to predict every person's outcome. It is cross-fitted in two folds,
    so that no control's prediction comes from a model fitted to its own
    outcome. The treated persons' outcomes are never used.
    """
    from sklearn.ensemble import HistGradientBoostingRegressor
    fold = np.random.default_rng(seed).integers(0, 2, len(D))
    c = np.where(D == 0)[0]
    p = np.zeros(len(D))
    for f in (0, 1):
        tr = c[fold[c] != f]
        model = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.05, random_state=0)
        p[fold == f] = model.fit(Q[tr], y[tr]).predict(Q[fold == f])
    return p


def predicted_bias(p, wt, wc):
    """The imbalance in the prognostic score, in dollars: a predicted bias."""
    return float(wmean(p, wt) - wmean(p, wc))
