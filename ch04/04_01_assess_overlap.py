#!/usr/bin/env python3
"""
Script 4.1 — Assessing common support
======================================
Chapter 4, Section 4.2. Produces Table 4.1.

Four counts and a region, computed on both scores of Chapter 3, so that the
difference between the estimators is visible in one place. None of this uses
the outcome.

    python ch04/04_01_assess_overlap.py
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common4 import cli, banner, score
import numpy as np, pandas as pd


def counts(ps, D):
    tr, ct = ps[D == 1], ps[D == 0]
    dec = pd.crosstab(pd.qcut(ps, 10, labels=False, duplicates="drop"), D)
    return {
        "Score range": f"{ps.min():.3f} to {ps.max():.3f}",
        "Treated above the highest control": f"{int((tr > ct.max()).sum()):,}",
        "Controls below the lowest treated": f"{int((ct < tr.min()).sum()):,}",
        "Persons with a score above 0.5": f"{int((ps > 0.5).sum()):,}",
        "Persons with a score above 0.7": f"{int((ps > 0.7).sum()):,}",
        # The decile with the fewest treated, and that same decile's size.
        # Until v4.8 the size was the smallest decile's, which is a different
        # decile whenever the two do not coincide.
        "Smallest decile treated cell": f"{int(dec[1].min()):,} of "
                                        f"{int(dec.loc[dec[1].idxmin()].sum()):,}",
    }


def main():
    a = cli(__doc__)
    res, region = {}, {}
    for label, est in [("logistic", "logit"), ("boosting", "gbm")]:
        s = score(a.datadir, est)
        ps, D = s["ps"], s["D"]
        res[label] = counts(ps, D)
        tr, ct = ps[D == 1], ps[D == 0]
        region[label] = (max(tr.min(), ct.min()), min(tr.max(), ct.max()))

    banner("Table 4.1 - overlap under the two scores of Chapter 3")
    print(f"  {'':36s} {'Logistic':>16s} {'Boosting':>16s}")
    for k in res["logistic"]:
        print(f"  {k:36s} {res['logistic'][k]:>16s} {res['boosting'][k]:>16s}")

    banner("The common support region (Fragment 4.1)")
    for k, (lo, hi) in region.items():
        print(f"  {k:10s} {lo:.3f} to {hi:.3f}")
    print("\n  The data are identical. The estimator is not. A reader using")
    print("  logistic regression may find the rest of this chapter unnecessary,")
    print("  and should record that they checked rather than that they trimmed.")


if __name__ == "__main__":
    main()
