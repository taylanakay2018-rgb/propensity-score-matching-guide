#!/usr/bin/env python3
"""
Script 2.3 — What is built into PLIDA-SIM
==========================================
Chapter 2, Section 2.3.

Two properties of the generator shape everything downstream: a shared latent
earnings capacity that drives selection and outcome alike, and the 2016
earnings shock. This script demonstrates both from the truth file, and shows
that reseeding produces an independent draw.

Uses truth_parameters.csv, which no analysis in the book may do.

    python ch02/02_03_plida_sim_properties.py
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common import cli, load, banner, deflate
import numpy as np, pandas as pd

def main():
    a = cli(__doc__)
    d = load(a.datadir, with_truth=True)
    t = d["truth"].set_index("person_id")
    D = t["treated"].values
    shock = t["earnings_shock_2016"].values

    banner("The effect, and why the naive comparison fails")
    y = np.where(D == 1, t["y1"], t["y0"])
    print(f"  true ATE                       ${t.tau_i.mean():>9,.0f}")
    print(f"  true ATT                       ${t.tau_i[D == 1].mean():>9,.0f}")
    print(f"  naive difference in means      ${y[D == 1].mean() - y[D == 0].mean():>9,.0f}   <- wrong sign")

    banner("The earnings shock: one confounder doing three jobs")
    inc = deflate(d["pit_income"], d["reference_indices"], ["salary_wages_nominal"])
    w = inc.pivot_table(index="person_id", columns="ref_year", values="salary_wages_real")
    w = w.reindex(t.index)
    pay = (d["domino_payments"].query("ref_year == 2016")
           .groupby("person_id")["fortnights_on_payment"].sum().reindex(t.index).fillna(0))
    for label, mask in [("shocked", shock == 1), ("not shocked", shock == 0)]:
        print(f"  {label:12s} n={mask.sum():>6,}  "
              f"2016 earnings ${w.loc[mask, 2016].mean():>8,.0f}  "
              f"fortnights {pay[mask].mean():4.1f}  "
              f"treated {100 * D[mask].mean():4.1f}%  "
              f"true effect ${t.tau_i[mask].mean():>7,.0f}")
    print("\n  It depresses earnings, drives income support, raises the chance of")
    print("  referral, and enlarges the treatment effect. That is what makes it")
    print("  a confounder rather than a nuisance — and Chapter 10 hides it.")

    banner("Selection on gains: why the ATT exceeds the ATE")
    print(f"  effect among the treated       ${t.tau_i[D == 1].mean():>9,.0f}")
    print(f"  effect among the untreated     ${t.tau_i[D == 0].mean():>9,.0f}")
    print(f"  the programme reaches people it helps more, by "
          f"{100 * (t.tau_i[D == 1].mean() / t.tau_i[D == 0].mean() - 1):.0f}%")

    banner("Reseeding")
    print("  python make_data.py --seed 20260809 --outdir plida_sim/draw_b")
    print("  Every result reported as an average across draws in this book was")
    print("  produced that way. Section 2.7.4 explains why it matters.")

if __name__ == "__main__":
    main()
