"""Shared helpers for the Chapter 4 scripts.

Chapter 4 works from the propensity score that Chapter 3 fitted, which in turn
works from the analysis file that Chapter 2 built. Every script here begins by
reproducing that score rather than reading a saved copy, so that a reader can
run any Chapter 4 script without having run Chapter 3 first.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ch03"))
from _common3 import (cli, banner, load_analysis, design_matrix,        # noqa: E402
                      eligible_only, fit_propensity, REPO)


def score(datadir: Path, estimator: str = "logit", with_truth: bool = False):
    """The Chapter 3 score on the eligible population, plus what scoring needs."""
    E = eligible_only(load_analysis(datadir, with_truth=with_truth))
    X = design_matrix(E)
    D = (E["_treated"] if with_truth else E["treated"]).values.astype(int)
    ps = fit_propensity(X, D, estimator, seed=20260808)
    out = {"E": E, "X": X, "D": D, "ps": ps}
    if with_truth:
        out["y"] = np.where(D == 1, E["_y1"], E["_y0"])
        out["tau"] = E["_tau_i"].values
    return out


def crump_alpha(ps: np.ndarray) -> float:
    """The variance-minimising threshold. See Fragment 4.2."""
    g = np.sort(1.0 / (ps * (1 - ps)))
    meets = g >= 2 * np.cumsum(g) / np.arange(1, len(g) + 1)
    if not meets.any():
        return 0.0
    lam = g[np.argmax(meets)]
    return 0.0 if lam <= 4 else float((1 - np.sqrt(1 - 4 / lam)) / 2)


def trimming_rules(ps: np.ndarray, D: np.ndarray) -> dict:
    """The seven rules of Table 4.2, as keep-masks.

    Each is a fact about where comparison is possible, with the deliberate
    exception of rule 7, which is a fact about the treated alone and is kept
    here because Section 4.6 needs it.
    """
    tr, ct = ps[D == 1], ps[D == 0]
    a = crump_alpha(ps)
    return {
        "0  no trimming": np.ones(len(ps), bool),
        "1  strict common support":
            (ps >= max(tr.min(), ct.min())) & (ps <= min(tr.max(), ct.max())),
        "2  1st-99th pct of treated":
            (ps >= np.percentile(tr, 1)) & (ps <= np.percentile(tr, 99)),
        "3  fixed 0.05 to 0.95": (ps >= 0.05) & (ps <= 0.95),
        "4  fixed 0.10 to 0.90": (ps >= 0.10) & (ps <= 0.90),
        "5  variance-minimising": (ps >= a) & (ps <= 1 - a),
        "6  asymmetric, below lowest treated": ~((D == 0) & (ps < tr.min())),
        "7  asymmetric, treated 5th pct": ~((D == 0) & (ps < np.percentile(tr, 5))),
    }


def ate_ipw(ps, D, y):
    w = np.where(D == 1, 1 / ps, 1 / (1 - ps))
    m1 = np.average(y[D == 1], weights=w[D == 1])
    m0 = np.average(y[D == 0], weights=w[D == 0])
    # The influence function of the normalised estimator, centred on each
    # group's weighted mean. Until v5.0 this used the unnormalised estimator's
    # influence function, D*y/ps - (1-D)*y/(1-ps), which overstated the
    # standard error by about 65 per cent. See Section 6.10.
    psi = D * (y - m1) / ps - (1 - D) * (y - m0) / (1 - ps)
    return m1 - m0, psi.std(ddof=1) / np.sqrt(len(y))


def att_odds(ps, D, y):
    """Odds weighting, which Chapter 6 develops properly."""
    w = np.where(D == 1, 1.0, ps / (1 - ps))
    m0 = np.average(y[D == 0], weights=w[D == 0])
    m1 = y[D == 1].mean()
    # Treated term centred on the treated mean (v5.0; previously on m0, which
    # added the estimate itself to the spread and overstated it by about 2%).
    psi = (D * (y - m1) - (1 - D) * w * (y - m0)) / D.mean()
    return m1 - m0, psi.std(ddof=1) / np.sqrt(len(y))
