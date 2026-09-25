#!/usr/bin/env python3
"""
Script 6.1 — Building the weights
==================================
Chapter 6, Section 6.3. Produces Table 6.1.

The weights for the ATE and for the ATT, on both scores of Chapter 3, with the
diagnostics that should be reported beside any weighted estimate: the largest
weight, the effective sample size, and how much of the control group's total
weight a handful of persons carry. The outcome is not touched.

    python ch06/06_01_build_weights.py
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common6 import (cli, banner, score, ate_weights, stabilised_weights,
                      att_weights, kish)
import numpy as np


def top_share(w, share=0.01):
    """Fraction of the total weight held by the heaviest `share` of persons."""
    s = np.sort(w)[::-1]
    k = max(1, int(round(share * len(s))))
    return s[:k].sum() / s.sum()


def table_6_1(datadir):
    """The rows of Table 6.1, as printed. audit.py uses this too."""
    res = {}
    for lab, est in (("logistic", "logit"), ("boosting", "gbm")):
        s = score(datadir, est)
        D, ps = s["D"], s["ps"]
        w, sw, wo = ate_weights(ps, D), stabilised_weights(ps, D), att_weights(ps, D)
        res[lab] = {
            "Largest ATE weight": f"{w.max():.1f}",
            "Largest stabilised ATE weight": f"{sw.max():.1f}",
            "Effective treated sample, ATE": f"{kish(w[D == 1]):,.0f} of {int(D.sum()):,}",
            "Effective control sample, ATE": f"{kish(w[D == 0]):,.0f} of {int((D == 0).sum()):,}",
            "Largest control odds weight": f"{wo[D == 0].max():.2f}",
            "Effective control sample, ATT": f"{kish(wo[D == 0]):,.0f} of {int((D == 0).sum()):,}",
            "Heaviest 1% of controls, ATT": f"{100 * top_share(wo[D == 0]):.1f}% of the weight",
        }
    return res


def main():
    a = cli(__doc__)
    res = table_6_1(a.datadir)
    banner("Table 6.1 - the weights, and what to report beside them")
    print(f"  {'':34s} {'Logistic':>22s} {'Boosting':>22s}")
    for k in res["logistic"]:
        print(f"  {k:34s} {res['logistic'][k]:>22s} {res['boosting'][k]:>22s}")

    # Fragment 6.1: the two sets of weights, written out
    print("\n  Under odds weighting every treated person counts once, and each control")
    print("  counts in proportion to how closely they resemble a treated person.")
    print("  The ATE weights instead reweight both groups toward the whole sample,")
    print("  so the rare treated persons with low scores carry the most weight.")


if __name__ == "__main__":
    main()
