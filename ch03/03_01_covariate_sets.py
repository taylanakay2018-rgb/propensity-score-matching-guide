#!/usr/bin/env python3
"""
Script 3.1 — The covariate set entering the propensity model
=============================================================
Chapter 3, Section 3.3. Produces Table 3.1.

Restates the three covariate lists declared in Chapter 2 and builds the design
matrix from them. Nothing here selects covariates: a set adjusted after seeing
model output is a set selected on the outcome.

    python ch03/03_01_covariate_sets.py
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common3 import cli, banner, load_analysis, design_matrix, eligible_only, HELD_BACK

ROLES = [
    ("age_2016", "Confounder", "Level"),
    ("sex", "Confounder", "Binary indicator"),
    ("dependent_children", "Confounder", "Count, median imputed"),
    ("highest_edu", "Confounder", "Ordinal, 0 to 4"),
    ("remoteness_area", "Confounder", "Ordinal, 0 to 3"),
    ("seifa_irsd_decile", "Confounder", "Decile, 1 to 10"),
    ("fortnights", "Confounder", "Count, 0 to 26"),
    ("lts", "Confounder", "Binary persistence indicator"),
    ("gp_attendances", "Confounder", "Count"),
    ("mh_item_flag", "Confounder", "Binary"),
    ("earnings_2014/15/16", "Confounder", "log(1 + x), three columns"),
    ("earnings_drop_2016", "Confounder", "Proportional fall, 2015 to 2016"),
    ("missingness indicators", "Confounder", "Four binary flags"),
    ("occupation_group", "Pure outcome predictor", "Held back; Chapter 6"),
    ("mutual_obligation_status", "Near-instrument", "Held back; Section 3.7"),
    ("referral_type", "Post-treatment", "Excluded; Section 2.4.4"),
]


def main():
    a = cli(__doc__)
    A = load_analysis(a.datadir)
    banner("Table 3.1 - what enters the propensity model")
    print(f"  {'Covariate':26s} {'Role':24s} Form")
    for name, role, form in ROLES:
        print(f"  {name:26s} {role:24s} {form}")

    E = eligible_only(A)
    X = design_matrix(E)
    banner("The design matrix (Section 3.3.5: eligible population)")
    print(f"  all persons        {len(A):,}")
    print(f"  eligible           {len(E):,}  ({100*len(E)/len(A):.1f}%)")
    print(f"  treated, eligible  {int(E['treated'].sum()):,}  ({100*E['treated'].mean():.2f}%)")
    print(f"  design matrix      {X.shape[0]:,} rows x {X.shape[1]} columns")
    print(f"  held back          {', '.join(HELD_BACK)}")
    assert not X.isna().any().any(), "design matrix must be complete before fitting"
    print("\n  [ok] no missing values reach the model")


if __name__ == "__main__":
    main()
