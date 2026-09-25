#!/usr/bin/env python3
"""
Script 4.4 — Who the trimming rule removes
===========================================
Chapter 4, Section 4.4.3. Produces Table 4.5.

Every trimmed analysis should report this, and most do not. Trimming changes
the population the estimate describes, and the only defence is to describe the
persons removed so that a reader can judge what changed.

    python ch04/04_04_who_is_removed.py
    python ch04/04_04_who_is_removed.py --rule "5  variance-minimising"
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common4 import cli, banner, score, trimming_rules
import numpy as np

DESCRIBE = [("Mean age", "age_2016", "{:.1f}"),
            ("Mean fortnights on payment", "fortnights", "{:.1f}"),
            ("Mean 2016 earnings", "earnings_2016", "${:,.0f}"),
            ("Mean SEIFA decile", "seifa_irsd_decile", "{:.1f}")]
DEFAULT_RULE = "3  fixed 0.05 to 0.95"


def main():
    a = cli(__doc__)
    rule = a.rule or DEFAULT_RULE
    s = score(a.datadir, "logit", with_truth=True)
    E, ps, D, tau = s["E"], s["ps"], s["D"], s["tau"]
    R = trimming_rules(ps, D)
    if rule not in R:
        sys.exit(f"No such rule: {rule!r}\nAvailable:\n  " + "\n  ".join(R))
    keep = R[rule]
    drop = ~keep

    banner(f"Table 4.5 - who the rule removes  [{rule}]")
    print(f"  {'':30s} {'Retained':>12s} {'Removed':>12s}")
    print(f"  {'Persons':30s} {keep.sum():12,} {drop.sum():12,}")
    for label, col, fmt in DESCRIBE:
        v = E[col].fillna(0).values
        print(f"  {label:30s} {fmt.format(v[keep].mean()):>12s} "
              f"{fmt.format(v[drop].mean()):>12s}")
    print(f"  {'Commenced the programme':30s} {100*D[keep].mean():11.1f}% "
          f"{100*D[drop].mean():11.1f}%")
    print(f"  {'True average effect':30s} {'$'+format(tau[keep].mean(),',.0f'):>12s} "
          f"{'$'+format(tau[drop].mean(),',.0f'):>12s}")
    shift = 100 * (tau[keep].mean() / tau.mean() - 1)
    print(f"\n  The removed are {100*drop.mean():.1f} per cent of the eligible population.")
    print(f"  Removing them moves the true average effect by {shift:+.1f} per cent,")
    print(f"  from ${tau.mean():,.0f} to ${tau[keep].mean():,.0f}.")
    print("\n  Part of any improvement in bias is the truth moving toward the")
    print("  estimate rather than the estimate moving toward the truth.")


if __name__ == "__main__":
    main()
