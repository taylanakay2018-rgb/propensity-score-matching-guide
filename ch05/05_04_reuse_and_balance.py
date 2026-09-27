#!/usr/bin/env python3
"""
Script 5.4 — Reuse, the estimand, and balance
==============================================
Chapter 5, Sections 5.10, 5.11 and 5.15. Produces Table 5.8 and Figure 5.2.

Three checks that every matched sample should carry and most do not: how often
controls were reused, how many treated persons were discarded and what that
did to the estimand, and whether the matched sample balances.

The last of these produces the uncomfortable result of Section 5.15: two
matched samples pass every balance test and their estimates differ by fifteen
percentage points.

    python ch05/05_04_reuse_and_balance.py
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common5 import (cli, banner, score, nn_match, mahalanobis_match, smd)
import numpy as np, pandas as pd

KEY = [("log_inc_2016", "log earnings 2016"), ("fn_2016", "fortnights on payment"),
       ("lts", "long-term recipient"), ("age", "age"),
       ("edu", "highest education"), ("remote", "remoteness"),
       ("seifa", "SEIFA decile"), ("mh", "mental health item")]


def main():
    a = cli(__doc__)
    s = score(a.datadir, a.estimator, with_truth=True)
    X, D, ps, tau = s["X"], s["D"], s["ps"], s["tau"]

    banner("Control reuse, with replacement (Fragment 5.5)")
    for cal, lab in [(0.1, "caliper 0.1"), (1e9, "no caliper")]:
        mt, mc = nn_match(ps, D, cal, replace=True, ratio=1)
        v = pd.Series(mc).value_counts()
        print(f"  {lab:12s} pairs {len(mt):,}  distinct controls {v.size:,}  "
              f"used once {int((v == 1).sum()):,}  most-used {v.max()}")
    print("\n  The gap between pairs and distinct controls is what Chapter 9")
    print("  has to work with. The naive standard error ignores it.")

    banner("The unmatched treated, and the estimand (Fragment 5.6)")
    nt = int(D.sum())
    for cal in (0.2, 0.1, 0.02):
        mt, _ = nn_match(ps, D, cal, False, 1)
        um = nt - len(set(mt.tolist()))
        print(f"  caliper {cal:<5} unmatched {um:3,}   true ATT all ${tau[D==1].mean():,.0f}"
              f"   matched ${tau[mt].mean():,.0f}"
              f"   shift {100*(tau[mt].mean()/tau[D==1].mean()-1):+.2f}%")
    mt3, _ = nn_match(ps, D, 0.1, False, 3)
    print(f"  1:3 ratio    unmatched {nt-len(set(mt3.tolist())):3,}   "
          f"matched ${tau[mt3].mean():,.0f}"
          f"   shift {100*(tau[mt3].mean()/tau[D==1].mean()-1):+.2f}%")

    mt_ps, mc_ps = nn_match(ps, D, 0.1, False, 1)
    mt_mh, mc_mh = mahalanobis_match(X, D, ps, 0.1)
    banner("Table 5.8 - balance before and after matching")
    print(f"  {'Covariate':24s} {'Before':>9s} {'PS match':>10s} {'Mahalanobis':>12s}")
    rows = []
    for col, label in KEY:
        v = X[col].values
        pooled = np.sqrt((v[D == 1].var() + v[D == 0].var()) / 2)
        before = smd(v, D == 1, D == 0)
        after_ps = (v[mt_ps].mean() - v[mc_ps].mean()) / pooled
        after_mh = (v[mt_mh].mean() - v[mc_mh].mean()) / pooled
        rows.append((before, after_ps, after_mh))
        print(f"  {label:24s} {before:+9.3f} {after_ps:+10.3f} {after_mh:+12.3f}")
    r = np.abs(np.array(rows))
    print(f"  {'mean absolute':24s} {r[:,0].mean():9.3f} {r[:,1].mean():10.3f} "
          f"{r[:,2].mean():12.3f}")
    print(f"  {'largest absolute':24s} {r[:,0].max():9.3f} {r[:,1].max():10.3f} "
          f"{r[:,2].max():12.3f}")
    print(f"  {'above 0.1':24s} {int((r[:,0]>0.1).sum()):9d} {int((r[:,1]>0.1).sum()):10d} "
          f"{int((r[:,2]>0.1).sum()):12d}")
    print("\n  Both matched samples satisfy every conventional balance criterion.")
    print("  Their estimates differ by fifteen percentage points (Table 5.2).")
    print("  Balance on means is necessary and is not sufficient; Chapter 8")
    print("  develops the diagnostics that can tell these two apart.")

    _figure(rows, a.outdir)


def _figure(rows, outdir):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.linewidth": 0.8,
                         "axes.labelsize": 8.5, "xtick.labelsize": 7.5,
                         "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
                         "legend.frameon": False, "savefig.dpi": 300,
                         "savefig.bbox": "tight", "savefig.facecolor": "white"})
    labels = [l for _, l in KEY]
    before = [r[0] for r in rows]; aps = [r[1] for r in rows]; amh = [r[2] for r in rows]
    y = np.arange(len(labels))
    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    ax.scatter(before, y, s=34, facecolors="white", edgecolors="black",
               linewidths=0.9, marker="o", label="before matching", zorder=3)
    ax.scatter(aps, y, s=30, facecolors="black", edgecolors="black",
               marker="s", label="propensity score", zorder=3)
    ax.scatter(amh, y, s=34, facecolors="white", edgecolors="black",
               linewidths=0.9, marker="^", label="Mahalanobis", zorder=3)
    for x in (-0.1, 0.1):
        ax.axvline(x, color="black", linewidth=0.7, linestyle=(0, (4, 3)))
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_yticks(y); ax.set_yticklabels(labels)
    ax.set_xlabel("Standardised mean difference")
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=2)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    outdir.mkdir(parents=True, exist_ok=True)
    for ext in ("tif", "png"):
        fig.savefig(outdir / f"figure_5_2_balance.{ext}")
    print(f"\n  wrote figure_5_2_balance.tif to {outdir}")


if __name__ == "__main__":
    main()
