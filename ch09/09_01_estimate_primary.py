#!/usr/bin/env python3
"""
Script 9.1 — The estimates, with their standard errors, on the primary dataset
==============================================================================
Chapter 9, Sections 9.2, 9.3, 9.7 and 9.8. Produces Table 9.1 and the figures
quoted in Sections 9.3, 9.7 and 9.8.

This is the point at which the book examines the 2019 earnings for the first
time as an analyst would: every design of Chapters 5 to 7 is estimated on the
primary dataset, with the standard error the earlier chapters quoted and the
one Section 9.9 recommends, and a 95 per cent interval in 2019 dollars. The
bootstrap uses 200 replicates, refitting the score each time. The truth file
is read only for the closing comparison.

    python ch09/09_01_estimate_primary.py
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common9 import (cli, banner, score, outcome_design, all_standard_errors, LABELS)
import numpy as np, pandas as pd

B = 200
SHOWN = ["odds", "dr_att", "sub20", "sub20_reg", "match", "match_repl", "maha", "maha13",
         "ipw_ate", "dr_ate"]
QUOTED = {"odds": "se_naive", "ipw_ate": "se_naive", "dr_att": "se_naive", "dr_ate": "se_naive",
          "sub20": "se_naive", "sub20_reg": None, "match": "se_paired",
          "match_repl": "se_paired", "maha": "se_paired", "maha13": "se_paired"}
RECOMMENDED = {"odds": "se_sandwich", "ipw_ate": "se_sandwich", "dr_att": "se_boot",
               "dr_ate": "se_boot", "sub20": "se_boot", "sub20_reg": "se_boot",
               "match": "se_paired", "match_repl": "se_ai", "maha": "se_paired",
               "maha13": "se_paired"}
NAMES = {"se_naive": "score known", "se_sandwich": "sandwich", "se_boot": "bootstrap",
         "se_paired": "paired", "se_ai": "Abadie-Imbens"}


def main():
    a = cli(__doc__)
    sc = score(a.datadir, "logit", with_truth=True)
    E, X, D, ps, y, tau = sc["E"], sc["X"], sc["D"], sc["ps"], sc["y"], sc["tau"]
    Q = outcome_design(E, X, with_occupation=True)
    t, reps = all_standard_errors(X, D, y, Q, ps, tau, seed=20260808, B=B)
    t = t.set_index("estimator")
    a.outdir.mkdir(parents=True, exist_ok=True)
    diffs = pd.DataFrame({"dr_less_odds": reps["dr_att"] - reps["odds"],
                          "reg_less_sub20": reps["sub20_reg"] - reps["sub20"]})
    t.assign(truth_att=tau[D == 1].mean(), truth_ate=tau.mean(),
             se_diff_dr_odds=diffs.dr_less_odds.std(ddof=1),
             se_diff_reg_sub=diffs.reg_less_sub20.std(ddof=1),
             corr_dr_odds=np.corrcoef(reps["dr_att"], reps["odds"])[0, 1]
             ).to_csv(a.outdir / "primary_estimates.csv")

    banner("Table 9.1 - the estimates on the primary dataset, 2019 dollars")
    print(f"  {'':34s} {'Estimate':>9s} {'SE quoted':>10s} {'SE':>7s} {'':14s} {'95% interval':>19s}")
    for k in SHOWN:
        r = t.loc[k]
        q = "" if QUOTED[k] is None else f"{r[QUOTED[k]]:,.0f}"
        se = r[RECOMMENDED[k]]
        print(f"  {LABELS[k]:34s} {r.est:9,.0f} {q:>10s} {se:7,.0f} {NAMES[RECOMMENDED[k]]:14s} "
              f"{r.est - 1.96 * se:9,.0f} to {r.est + 1.96 * se:,.0f}")
    print(f"\n  treated persons {int(D.sum()):,}; controls {int((D == 0).sum()):,}; "
          f"bootstrap replicates {B}")

    banner("Section 9.3 - what each correction changes, primary dataset")
    o, ia = t.loc["odds"], t.loc["ipw_ate"]
    print(f"  odds weighting: score known {o.se_naive:,.0f}, sandwich {o.se_sandwich:,.0f}, "
          f"bootstrap {o.se_boot:,.0f}")
    print(f"  normalised IPW: score known {ia.se_naive:,.0f}, sandwich {ia.se_sandwich:,.0f}, "
          f"bootstrap {ia.se_boot:,.0f}")
    m, r_ = t.loc["match"], t.loc["match_repl"]
    print(f"  PS matching 1:1: paired {m.se_paired:,.0f}, unpaired {m.se_unpaired:,.0f}, "
          f"matched-set bootstrap {m.se_boot_sets:,.0f}, bootstrap {m.se_boot:,.0f}")
    print(f"  with replacement: paired {r_.se_paired:,.0f}, Abadie-Imbens {r_.se_ai:,.0f}; "
          f"{int(r_.pairs):,} pairs, {int(r_.distinct):,} distinct controls, largest reuse "
          f"{int(r_.max_reuse)}")
    print(f"  weighted regression, odds weights: default {o.se_wls_default:,.0f}, "
          f"robust {o.se_wls_robust:,.0f}; IPW weights: default {ia.se_wls_default:,.0f}, "
          f"robust {ia.se_wls_robust:,.0f}")

    banner("Section 9.7 - the standard error of a difference, primary dataset")
    d = reps["dr_att"] - reps["odds"]
    unp = np.sqrt(t.loc["dr_att", "se_boot"] ** 2 + t.loc["odds", "se_boot"] ** 2)
    print(f"  doubly robust less odds weighting: {t.loc['dr_att', 'est'] - t.loc['odds', 'est']:+,.0f}; "
          f"bootstrap SE of the difference {d.std(ddof=1):,.0f}, against {unp:,.0f} if the "
          f"two were independent; correlation {np.corrcoef(reps['dr_att'], reps['odds'])[0, 1]:.2f}")
    d = reps["sub20_reg"] - reps["sub20"]
    print(f"  20 strata with regression less without: "
          f"{t.loc['sub20_reg', 'est'] - t.loc['sub20', 'est']:+,.0f}; bootstrap SE of the "
          f"difference {d.std(ddof=1):,.0f}")

    banner("Section 9.8 - scoring the estimates on the primary dataset")
    print(f"  true ATT ${tau[D == 1].mean():,.0f}; true ATE ${tau.mean():,.0f}")
    for k in SHOWN[:-2]:
        r = t.loc[k]
        se = r[RECOMMENDED[k]]
        inside = abs(r.est - r.truth) <= 1.96 * se
        print(f"  {LABELS[k]:34s} truth for the persons described ${r.truth:,.0f}: "
              f"{'inside' if inside else 'outside'} the interval")


if __name__ == "__main__":
    main()
