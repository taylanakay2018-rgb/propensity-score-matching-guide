"""Shared helpers for the Chapter 3 scripts.

Chapter 3 works from the analysis file that Chapter 2 produced, so every script
here begins by loading it rather than by re-linking the modules. If the file is
absent the loader says which Chapter 2 script to run first.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ch02"))
from _common import cli, banner, REPO, DEFAULT_DATA          # noqa: E402

BASELINE_YEAR = 2016

# Declared in Chapter 2, restated here rather than reselected. See Table 3.1.
HELD_BACK = ["occupation_group", "mutual_obligation_status"]


def load_analysis(datadir: Path, with_truth: bool = False) -> pd.DataFrame:
    """The Chapter 2 analysis file, with a message rather than a traceback."""
    f = datadir / "analysis_file.csv"
    if not f.exists():
        sys.exit(
            f"No analysis file at {f}.\n"
            f"Chapter 3 starts from Chapter 2's output. Build it first:\n"
            f"    python ch02/02_05_link_modules.py --datadir {datadir}\n"
            f"    python ch02/02_06_reshape_panel.py --datadir {datadir}"
        )
    a = pd.read_csv(f).set_index("person_id")
    if with_truth:
        tp = datadir / "truth" / "truth_parameters.csv"
        if not tp.exists():
            sys.exit(
                f"This script scores against {tp.name}, which is not in {datadir}.\n\n"
                "The exercise variant ships without it on purpose. Use the primary\n"
                "dataset, or generate a copy with the truth file included:\n\n"
                f"    python make_data.py --outdir {datadir.parent / 'plida_sim_a'}"
            )
        t = pd.read_csv(tp).set_index("person_id").reindex(a.index)
        for c in ("treated", "y0", "y1", "tau_i"):
            a[f"_{c}"] = t[c].values
    return a


def design_matrix(a: pd.DataFrame) -> pd.DataFrame:
    """The eighteen columns of Table 3.1, in the forms Section 3.3.2 settles on."""
    X = pd.DataFrame(index=a.index)
    X["age"] = a["age_2016"]
    X["female"] = (a["sex"] == "Female").astype(int)
    X["kids"] = a["dependent_children"].fillna(a["dependent_children"].median())
    X["edu"] = a["highest_edu"].map(
        {"<Year 12": 0, "Year 12": 1, "Cert III/IV": 2, "Diploma": 3, "Bachelor+": 4})
    X["edu"] = X["edu"].fillna(X["edu"].median())
    X["remote"] = a["remoteness_area"].map(
        {"Major Cities": 0, "Inner Regional": 1, "Outer Regional": 2, "Remote+": 3})
    X["seifa"] = a["seifa_irsd_decile"]
    X["fn_2016"] = a["fortnights"]
    X["lts"] = (a["fortnights"] >= 20).astype(int)
    X["gp"] = a["gp_attendances"]
    X["mh"] = a["mh_item_flag"]
    for y in (2014, 2015, 2016):                 # all three years, per Section 2.6.2
        col = a[f"earnings_{y}"]
        X[f"log_inc_{y}"] = np.log1p(col)
        X[f"inc_{y}_missing"] = col.isna().astype(int)
        X[f"log_inc_{y}"] = X[f"log_inc_{y}"].fillna(X[f"log_inc_{y}"].median())
    X["drop_2016"] = a["earnings_drop_2016"].fillna(0)
    X["drop_missing"] = a["earnings_drop_2016"].isna().astype(int)
    return X


def fit_propensity(X: pd.DataFrame, D, estimator: str = "logit", seed: int = 0):
    """Logistic regression with regularisation off, or gradient boosting."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import GradientBoostingClassifier
    if estimator == "logit":
        Z = (X - X.mean()) / X.std().replace(0, 1)
        # C is large on purpose: shrinking a confounder under-adjusts for it.
        return LogisticRegression(max_iter=5000, C=1e6).fit(Z, D).predict_proba(Z)[:, 1]
    return (GradientBoostingClassifier(n_estimators=200, max_depth=3,
                                       learning_rate=0.1, random_state=seed)
            .fit(X, D).predict_proba(X)[:, 1])


def stabilised_weights(ps, D):
    p = np.mean(D)
    return np.where(D == 1, p / ps, (1 - p) / (1 - ps))


def effective_n(w):
    """Kish effective sample size."""
    return float(w.sum() ** 2 / (w ** 2).sum())


def match(ps, D, caliper: float = 0.1):
    """1:1 nearest neighbour on the linear predictor. Chapter 5 does this properly."""
    from sklearn.neighbors import NearestNeighbors
    q = np.clip(ps, 1e-6, 1 - 1e-6)
    lo = np.log(q / (1 - q))
    t, c = np.where(D == 1)[0], np.where(D == 0)[0]
    nn = NearestNeighbors(n_neighbors=1).fit(lo[c].reshape(-1, 1))
    d, i = nn.kneighbors(lo[t].reshape(-1, 1))
    k = d.ravel() <= caliper * lo.std()
    return t[k], c[i.ravel()[k]], int((~k).sum())


def matched_bias(mt, mc, y, tau):
    """Percentage bias against the true ATT for the matched treated."""
    diff = y[mt] - y[mc]
    truth = tau[mt].mean()
    return 100 * (diff.mean() - truth) / truth, diff.mean(), diff.std(ddof=1) / np.sqrt(len(diff))


def eligible_only(a: pd.DataFrame) -> pd.DataFrame:
    """Section 3.3.5: the flag is applied once, in Chapter 2, and reused here."""
    return a[a["eligible"] == 1]
