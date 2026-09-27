#!/usr/bin/env python3
"""
Script 5.2 — The nine matching variants
========================================
Chapter 5, Section 5.4. Builds the nine matched datasets.

One draw only. The comparison between variants needs several draws to mean
anything, and Script 5.3 does that; this script exists so that a reader can
see each construction and what it produces without waiting eight minutes.

    python ch05/05_02_match_variants.py
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common5 import (cli, banner, score, nn_match, mahalanobis_match,
                      matched_att)
import numpy as np, pandas as pd


def variants(ps, D, X):
    v = [(f"NN 1:1, caliper {c}", lambda c=c: nn_match(ps, D, c, False, 1))
         for c in (0.2, 0.1, 0.05, 0.02)]
    return ([("NN 1:1, no caliper", lambda: nn_match(ps, D, 1e9, False, 1))] + v +
            [("NN 1:1 with replacement, caliper 0.1", lambda: nn_match(ps, D, 0.1, True, 1)),
             ("NN 1:2, caliper 0.1", lambda: nn_match(ps, D, 0.1, False, 2)),
             ("NN 1:3, caliper 0.1", lambda: nn_match(ps, D, 0.1, False, 3)),
             ("Mahalanobis within caliper 0.1", lambda: mahalanobis_match(X, D, ps, 0.1))])


def main():
    a = cli(__doc__)
    s = score(a.datadir, a.estimator, with_truth=True)
    X, D, ps, y, tau = s["X"], s["D"], s["ps"], s["y"], s["tau"]
    nt = int(D.sum())

    banner("The nine matched datasets (one draw; Script 5.3 repeats them across six)")
    print(f"  {'Variant':38s} {'Bias':>8s} {'Pairs':>8s} {'Unmat':>6s} {'Reuse':>6s}")
    for name, fn in variants(ps, D, X):
        mt, mc = fn()
        bias, _, _ = matched_att(mt, mc, y, tau)
        reuse = pd.Series(mc).value_counts().max() if len(mc) else 0
        print(f"  {name:38s} {bias:+7.1f}% {len(mt):8,} "
              f"{nt - len(set(mt.tolist())):6,} {int(reuse):6,}")
    print("\n  One draw cannot separate these. Script 5.3 repeats them across six,")
    print("  which is the whole point of Sections 5.5 and 5.6.")


if __name__ == "__main__":
    main()
