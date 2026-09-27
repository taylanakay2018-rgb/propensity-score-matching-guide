#!/usr/bin/env python3
"""
Script 5.1 — Building a first matched sample
=============================================
Chapter 5, Section 5.3. Produces Table 5.1 and one matched dataset.

Four chapters in five lines: Chapter 2's eligibility flag, Chapter 3's score,
Chapter 4's trimming rule, and this chapter's matching. The two assertions at
the end are the equivalent of the merge guards of Section 2.5.4.

    python ch05/05_01_match_basics.py
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common5 import (cli, banner, score, trimming_rules, nn_match,
                      mahalanobis_match, MAHA_COLS)
import numpy as np, pandas as pd

DECISIONS = [
    ("Distance", "propensity score / linear predictor / Mahalanobis", "what similar means"),
    ("Caliper", "none / 0.2 / 0.1 / 0.05 / 0.02 SD", "how close is close enough"),
    ("Replacement", "with / without", "can a control serve twice"),
    ("Ratio", "1:1 / 1:2 / 1:3", "how many controls each"),
    ("Order", "greedy descending / optimal", "who chooses first"),
]


def main():
    a = cli(__doc__)
    banner("Table 5.1 - the five decisions in a matching procedure")
    print(f"  {'Decision':14s} {'Options in common use':46s} Controls")
    for d, o, w in DECISIONS:
        print(f"  {d:14s} {o:46s} {w}")

    s = score(a.datadir, a.estimator)
    E, X, D, ps = s["E"], s["X"], s["D"], s["ps"]
    keep = trimming_rules(ps, D)["5  variance-minimising"]   # Chapter 4's choice
    banner("Four chapters in five lines (Fragment 5.2)")
    print(f"  eligible persons        {len(E):,}")
    print(f"  retained after trimming {int(keep.sum()):,}")

    Xk, Dk, psk = X[keep], D[keep], ps[keep]
    mt, mc = nn_match(psk, Dk, caliper=0.1, replace=False, ratio=1)
    print(f"  matched pairs           {len(mt):,}")
    print(f"  treated unmatched       {int(Dk.sum()) - len(set(mt.tolist())):,}")

    # Fragment 5.3: assembling the frame, with the assertions worth making.
    Ek = E[keep]
    matched = pd.concat([
        Ek.iloc[mt].assign(arm=1, pair=np.arange(len(mt))),
        Ek.iloc[mc].assign(arm=0, pair=np.arange(len(mc))),
    ])
    assert len(matched) == 2 * len(mt), "repeats must survive the assembly"
    assert matched.groupby("pair").size().eq(2).all(), "every pair needs two rows"
    print(f"  matched frame           {len(matched):,} rows, {matched.pair.nunique():,} pairs")
    print("\n  [ok] the frame has two rows per pair and no pair was collapsed")

    out = a.datadir / "matched_sample.csv"
    matched.to_csv(out)
    print(f"  written to {out}")
    print("\n  The outcome has not been touched. Chapter 8 checks this sample for")
    print("  balance and Chapter 9 estimates its standard error properly.")


if __name__ == "__main__":
    main()
