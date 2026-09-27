#!/usr/bin/env python3
"""
Script 2.6 — From panel to cross-section
=========================================
Chapter 2, Section 2.6. Produces Table 2.5 and the analysis file.

Collapses 300,000 person-years to one row per person, deflates to constant
2019 dollars, and constructs the trajectory covariates. This script produces
the file every later chapter starts from.

    python ch02/02_06_reshape_panel.py
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common import cli, load, banner, safe_merge, deflate, smd, BASELINE_YEAR, YEARS
import numpy as np, pandas as pd

B = BASELINE_YEAR

def main():
    a = cli(__doc__)
    d = load(a.datadir)
    linked = a.datadir / "linked_2016.csv"
    if not linked.exists():
        sys.exit(f"Run 02_05_link_modules.py first: {linked} not found")
    A = pd.read_csv(linked)

    banner("Deflation (Section 2.6.5)")
    inc = deflate(d["pit_income"], d["reference_indices"], ["salary_wages_nominal"])
    wide = (inc.pivot_table(index="person_id", columns="ref_year",
                            values="salary_wages_real").add_prefix("earnings_"))
    # The payment total came through the link in nominal dollars. Deflate it
    # here and drop the nominal column, or the invariant at the foot of this
    # script will fail -- which is the point of having the invariant.
    cpi_2016 = float(d["reference_indices"].set_index("ref_year").loc[B, "cpi_index"])
    A["payment_amount_real"] = A["payment_amount_nominal"] / (cpi_2016 / 100)
    # The 2016 income columns arrived through the link in nominal dollars and
    # are superseded by the deflated wide columns joined below. Drop them
    # rather than carry two versions of the same quantity in different units.
    A = A.drop(columns=["payment_amount_nominal", "salary_wages_nominal",
                        "total_income_nominal"])
    print(f"  {len(inc):,} person-years deflated to constant 2019 AUD")
    print(f"  payment totals deflated at the {B} index ({cpi_2016:.1f})")
    print("  nominal columns keep the _nominal suffix so a units error raises KeyError")

    banner("Table 2.5 — the same covariate, three reference years")
    A = A.set_index("person_id").join(wide)
    D = A["treated"].values == 1
    print(f"  {'Year':10s} {'Observed':>10s} {'Mean':>12s} {'Std. diff.':>12s}")
    for y in (2014, 2015, 2016):
        c = f"earnings_{y}"
        v = A[c].values
        ok = ~np.isnan(v)
        print(f"  {y} (t-{B-y+1})  {100*ok.mean():9.1f}% ${A[c].mean():>11,.0f} "
              f"{smd(np.nan_to_num(v, nan=np.nanmean(v)), D, ~D):>12.3f}")

    banner("Trajectory covariates (Section 2.6.2)")
    A["earnings_drop_2016"] = 1 - A["earnings_2016"] / A["earnings_2015"]
    pre = A[[f"earnings_{y}" for y in (2014, 2015, 2016)]]
    A["earnings_volatility"] = pre.std(axis=1) / pre.mean(axis=1)
    for c in ("earnings_drop_2016", "earnings_volatility"):
        v = A[c].values; ok = ~np.isnan(v)
        print(f"  {c:22s} defined for {100*ok.mean():4.1f}%   "
              f"std. diff. {smd(v[ok], D[ok], ~D[ok]):+.3f}")
    print("\n  A ratio of two partially observed variables compounds their")
    print("  missingness. Check the denominator before you trust the column.")

    banner("The finished analysis file (Section 2.6.6)")
    A["age_2016"] = B - A["birth_year"]
    groups = {
        "identifier": ["(index) person_id"],
        "flags": ["treated", "eligible"],
        "confounders": ["age_2016", "sex", "highest_edu", "dependent_children",
                        "english_proficiency", "remoteness_area", "seifa_irsd_decile",
                        "fortnights", "gp_attendances", "mh_item_flag",
                        "earnings_2014", "earnings_2015", "earnings_2016",
                        "earnings_drop_2016", "earnings_volatility"],
        "pure outcome predictor": ["occupation_group"],
        "near-instrument": ["mutual_obligation_status"],
        "outcomes (do not touch until Chapter 9)": ["earnings_2019"],
    }
    for k, v in groups.items():
        print(f"  {k:40s} {len(v):>2d}  {', '.join(v[:4])}{' …' if len(v) > 4 else ''}")

    out = a.datadir / "analysis_file.csv"
    A.to_csv(out)
    # A.shape[1] excludes person_id, which to_csv writes as the first column.
    print(f"\n  {len(A):,} rows x {A.shape[1] + 1} columns written to {out}")

    banner("Invariants (Fragment 2.12)")
    checks = [
        ("one row per person", A.index.is_unique),
        ("treatment is binary", A["treated"].isin([0, 1]).all()),
        ("eligible ages in range", A.loc[A.eligible == 1, "age_2016"].between(22, 59).all()),
        ("no negative earnings", (A[[c for c in A if c.startswith("earnings_2")]].min().min() >= 0)),
        ("no nominal columns survive", not [c for c in A.columns if c.endswith("_nominal")]),
    ]
    for label, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {label}")
    if not all(ok for _, ok in checks):
        sys.exit("invariant failed")

if __name__ == "__main__":
    main()
