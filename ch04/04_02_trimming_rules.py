#!/usr/bin/env python3
"""
Script 4.2 — The seven trimming rules
======================================
Chapter 4, Section 4.3. Produces Table 4.2.

Applies each rule to the fitted score and reports what it removes, separately
for the treated and the controls, because a rule that removes treated persons
changes the estimand of an effect on the treated and a rule that removes only
controls does not.

    python ch04/04_02_trimming_rules.py
    python ch04/04_02_trimming_rules.py --estimator gbm
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common4 import cli, banner, score, trimming_rules, crump_alpha
import numpy as np


def main():
    a = cli(__doc__)
    est = a.estimator
    s = score(a.datadir, est)
    ps, D = s["ps"], s["D"]
    R = trimming_rules(ps, D)

    banner(f"Table 4.2 - what each rule removes ({est} score)")
    print(f"  {'Rule':40s} {'Removed':>9s} {'Treated':>9s} {'Controls':>9s} {'Share':>8s}")
    for name, keep in R.items():
        drop = ~keep
        print(f"  {name:40s} {drop.sum():9,} {int((drop & (D == 1)).sum()):9,} "
              f"{int((drop & (D == 0)).sum()):9,} {100 * drop.mean():7.1f}%")
    print(f"\n  variance-minimising threshold alpha = {crump_alpha(ps):.4f}")
    print("\n  The rules span from one person in a thousand to more than half the")
    print("  sample. A report that says only that the sample was trimmed has")
    print("  said almost nothing.")


if __name__ == "__main__":
    main()
