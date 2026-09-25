#!/usr/bin/env python3
"""
Script 2.8 — Attrition
=======================
Chapter 2, Section 2.8. Produces Table 2.8.

Three exit routes between treatment and outcome, only two of them labelled.
Quantifies the rate, its differential by treatment arm, who leaves, and the
gap between the effect for survivors and the effect for the eligible
population.

    python ch02/02_08_attrition.py
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common import cli, load, banner, OUTCOME_YEAR
import numpy as np, pandas as pd

def main():
    a = cli(__doc__)
    d = load(a.datadir, with_truth=True)
    t = d["truth"].set_index("person_id")
    sp = d["spine_scoping"].set_index("person_id").reindex(t.index)
    D = t["treated"].values == 1
    n = len(t)

    banner("Table 2.8 — attrition by route")
    died = sp["deceased_year"].notna().values
    emig = sp["emigrated_year"].notna().values
    left = (sp["last_active_year"] < OUTCOME_YEAR).values
    lost = left & ~died & ~emig
    print(f"  {'Route':34s} {'Rate':>7s}  Labelled?")
    for label, m, lab in [("Death", died, "yes — deceased_year"),
                          ("Emigration", emig, "yes — emigrated_year"),
                          ("Left the in-scope population", lost, "NO — infer from last_active_year"),
                          ("Any of the three", left, "—")]:
        print(f"  {label:34s} {100*m.mean():6.2f}%  {lab}")
    print("\n  The largest route is the unlabelled one. Filtering on the two")
    print("  explicit fields addresses 4.3 points of a 13.2 point problem.")

    banner("It is differential, and it is selected")
    print(f"  attrition among participants     {100*left[D].mean():5.2f}%")
    print(f"  attrition among non-participants {100*left[~D].mean():5.2f}%")
    print(f"  differential                     {100*(left[D].mean()-left[~D].mean()):+5.2f} pp")
    shock = t["earnings_shock_2016"].values
    print(f"\n  earnings shock among leavers     {100*shock[left].mean():5.1f}%")
    print(f"  earnings shock among stayers     {100*shock[~left].mean():5.1f}%")
    print("  Attrition removes the people with the largest treatment effects.")

    banner("What that does to the estimand")
    tau = t["tau_i"].values
    print(f"  true ATT, full eligible population  ${tau[D].mean():>8,.0f}")
    print(f"  true ATT, survivors only            ${tau[D & ~left].mean():>8,.0f}   "
          f"({100*(tau[D & ~left].mean()/tau[D].mean()-1):+.1f}%)")
    print(f"  true ATE, full                      ${tau.mean():>8,.0f}")
    print(f"  true ATE, survivors only            ${tau[~left].mean():>8,.0f}   "
          f"({100*(tau[~left].mean()/tau.mean()-1):+.1f}%)")
    print("\n  This is not bias. It is a different quantity, and it exists")
    print("  before any estimator is applied. See Section 2.8.3.")

if __name__ == "__main__":
    main()
