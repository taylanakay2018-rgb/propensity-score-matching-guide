#!/usr/bin/env python3
"""
Script 3.3 — Estimating the propensity score by gradient boosting
==================================================================
Chapter 3, Section 3.6. Produces the boosted score.

scikit-learn is the canonical backend here, with the hyperparameters stated
below, because every number in Chapter 3 is reproducible from it and it
installs everywhere. causalml is offered with --causalml as an alternative,
but note that it is NOT the same model: its defaults fit far more aggressively
and produce a materially different score. That difference is itself the point
of Section 3.6, and Exercise 3.6 asks readers to quantify it.

    python ch03/03_03_estimate_gbm.py
    python ch03/03_03_estimate_gbm.py --causalml   # a different model, on purpose
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common3 import (cli, banner, load_analysis, design_matrix, eligible_only,
                      stabilised_weights, effective_n)
import numpy as np, pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score

PARAMS = dict(n_estimators=200, max_depth=3, learning_rate=0.1, random_state=20260808)


def boosted_score(X, D, use_causalml=False):
    """The canonical score is scikit-learn with the stated hyperparameters."""
    if not use_causalml:
        return GradientBoostingClassifier(**PARAMS).fit(X, D).predict_proba(X)[:, 1], "sklearn"
    try:
        from causalml.propensity import GradientBoostedPropensityModel
        return GradientBoostedPropensityModel().fit_predict(X.values, D), "causalml"
    except Exception as e:
        print(f"  causalml unavailable ({type(e).__name__}); falling back to scikit-learn")
        return GradientBoostingClassifier(**PARAMS).fit(X, D).predict_proba(X)[:, 1], "sklearn"


def main():
    a = cli(__doc__)
    E = eligible_only(load_analysis(a.datadir))
    X, D = design_matrix(E), E["treated"].values
    banner("Fitting the boosted score")
    ps, backend = boosted_score(X, D, use_causalml="--causalml" in sys.argv)

    w = stabilised_weights(ps, D)
    tr, ct = ps[D == 1], ps[D == 0]
    print(f"\n  backend             {backend}")
    print(f"  AUC                 {roc_auc_score(D, ps):.3f}")
    print(f"  range               {ps.min():.3f} to {ps.max():.3f}")
    print(f"  largest weight      {w.max():.1f}")
    print(f"  effective controls  {effective_n(w[D == 0]):,.0f}")
    print(f"  treated above the highest control score  {int((tr > ct.max()).sum()):,}")
    if backend == "sklearn":
        print("\n  Run with --causalml to see how far another library's defaults move")
        print("  this score. They are not interchangeable, and Section 3.6 says why.")
    print("\n  The score is fitted and predicted on the same rows, with no holdout.")
    print("  That is correct here: the score describes the assignment mechanism")
    print("  for these persons, and is not forecasting anything about new ones.")

    out = a.datadir / "propensity_gbm.csv"
    pd.DataFrame({"person_id": E.index, "ps_gbm": ps}).to_csv(out, index=False)
    print(f"  written to {out}")


if __name__ == "__main__":
    main()
