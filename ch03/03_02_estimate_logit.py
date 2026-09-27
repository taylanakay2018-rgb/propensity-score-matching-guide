#!/usr/bin/env python3
"""
Script 3.2 — Estimating the propensity score by logistic regression
====================================================================
Chapter 3, Section 3.4. Produces Table 3.2 and the logistic score.

Fits the recommended specification: the eighteen covariates of Table 3.1, on the
eligible population, with regularisation off.

    python ch03/03_02_estimate_logit.py
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common3 import (cli, banner, load_analysis, design_matrix, eligible_only,
                      fit_propensity, stabilised_weights, effective_n)
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

LABEL = {"remote": "remoteness_area", "log_inc_2016": "log earnings 2016",
         "fn_2016": "fortnights on payment", "age": "age_2016",
         "edu": "highest_edu", "seifa": "seifa_irsd_decile",
         "mh": "mh_item_flag", "lts": "lts (long-term recipient)"}


def main():
    a = cli(__doc__)
    E = eligible_only(load_analysis(a.datadir))
    X, D = design_matrix(E), E["treated"].values
    Z = (X - X.mean()) / X.std().replace(0, 1)
    m = LogisticRegression(max_iter=5000, C=1e6).fit(Z, D)
    ps = m.predict_proba(Z)[:, 1]

    p = np.clip(ps, 1e-9, 1 - 1e-9)
    W = p * (1 - p)
    Zi = np.c_[np.ones(len(Z)), Z.values]
    se = np.sqrt(np.diag(np.linalg.pinv(Zi.T @ (Zi * W[:, None]))))[1:]
    co = pd.Series(m.coef_[0], index=X.columns)
    sd = pd.Series(se, index=X.columns)

    banner("Table 3.2 - standardised logistic coefficients, eight largest")
    print(f"  {'Covariate':26s} {'Coef':>8s} {'SE':>7s} {'z':>7s}")
    for k in co.abs().sort_values(ascending=False).index[:8]:
        print(f"  {LABEL.get(k, k):26s} {co[k]:8.3f} {sd[k]:7.3f} {co[k]/sd[k]:7.1f}")
    print(f"\n  intercept {m.intercept_[0]:.3f}   AUC {roc_auc_score(D, ps):.3f}   n {len(X):,}")
    print("  Coefficients are partial associations within this specification.")
    print("  They are not causal effects, and significance is not a selection rule.")

    w = stabilised_weights(ps, D)
    banner("The fitted score")
    print(f"  range               {ps.min():.3f} to {ps.max():.3f}")
    print(f"  mean score          {ps.mean():.4f}   observed rate {D.mean():.4f}")
    print(f"  largest weight      {w.max():.1f}")
    print(f"  effective controls  {effective_n(w[D == 0]):,.0f} of {int((D == 0).sum()):,}")
    assert ps.max() < 1 and ps.min() > 0, "separation: a fitted probability hit 0 or 1"
    print("\n  [ok] no fitted probability is 0 or 1")

    out = a.datadir / "propensity_logit.csv"
    pd.DataFrame({"person_id": E.index, "ps_logit": ps}).to_csv(out, index=False)
    print(f"  written to {out}")


if __name__ == "__main__":
    main()
