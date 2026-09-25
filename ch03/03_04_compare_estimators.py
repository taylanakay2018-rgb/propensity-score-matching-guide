#!/usr/bin/env python3
"""
Script 3.4 — Logistic regression against gradient boosting
===========================================================
Chapter 3, Section 3.6.2. Produces Table 3.4.

Compares the two scores by consequence rather than by agreement. The
correlation of the scores is the quantity most often reported and is the wrong
one: two scores correlating at 0.92 give matched estimates 32 percentage
points apart, in opposite directions.

    python ch03/03_04_compare_estimators.py
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common3 import (cli, banner, load_analysis, design_matrix, eligible_only,
                      fit_propensity, stabilised_weights, match, matched_bias)
import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score


def main():
    a = cli(__doc__)
    E = eligible_only(load_analysis(a.datadir, with_truth=True))
    X = design_matrix(E)
    D = E["_treated"].values.astype(int)
    y = np.where(D == 1, E["_y1"], E["_y0"])
    tau = E["_tau_i"].values

    out = {}
    for lab, kind in [("logistic", "logit"), ("boosting", "gbm")]:
        ps = fit_propensity(X, D, kind, seed=20260808)
        w = stabilised_weights(ps, D)
        mt, mc, un = match(ps, D)
        bias, _, _ = matched_bias(mt, mc, y, tau)
        tr, ct = ps[D == 1], ps[D == 0]
        out[lab] = dict(auc=roc_auc_score(D, ps), lo=ps.min(), hi=ps.max(),
                        above=int((tr > ct.max()).sum()), unmatched=un,
                        maxw=w.max(), bias=bias, ps=ps)

    r = np.corrcoef(out["logistic"]["ps"], out["boosting"]["ps"])[0, 1]
    rs = spearmanr(out["logistic"]["ps"], out["boosting"]["ps"]).statistic

    # Table 3.4 takes its first three rows from this draw and the other four
    # from Script 3.5's five draws, which is what its caption says. Until v4.9
    # all seven were printed here under the Table 3.4 banner, four of them
    # single-draw values the book does not show.
    banner("Table 3.4 - the same covariates, two estimators (primary-dataset rows)")
    rows = [("Area under the ROC curve", "auc", "{:.3f}"),
            ("Treated above the highest control", "above", "{:,.0f}")]
    print(f"  {'':36s} {'Logistic':>12s} {'Boosting':>12s}")
    print(f"  {'Score range':36s} "
          f"{out['logistic']['lo']:.3f}-{out['logistic']['hi']:.3f}".ljust(52) +
          f"{out['boosting']['lo']:.3f}-{out['boosting']['hi']:.3f}")
    for label, key, fmt in rows:
        print(f"  {label:36s} {fmt.format(out['logistic'][key]):>12s} "
              f"{fmt.format(out['boosting'][key]):>12s}")
    print(f"\n  The two scores correlate at {r:.3f} (Pearson), {rs:.3f} (Spearman).")
    print("  Report that number and you would conclude the choice did not matter.")

    banner("The same comparison by consequence, on this draw alone")
    for label, key, fmt in [("Treated left unmatched", "unmatched", "{:,.0f}"),
                            ("Largest stabilised weight", "maxw", "{:.1f}"),
                            ("Bias of the matched estimate (%)", "bias", "{:+.1f}")]:
        print(f"  {label:36s} {fmt.format(out['logistic'][key]):>12s} "
              f"{fmt.format(out['boosting'][key]):>12s}")
    gap = out["boosting"]["bias"] - out["logistic"]["bias"]
    print(f"\n  On this draw the two estimates differ by {gap:.0f} percentage points.")
    print("  Table 3.4 reports these rows across five draws; Script 3.5 produces them.")


if __name__ == "__main__":
    main()
