#!/usr/bin/env python3
"""
Script 7.1 — Forming the strata
================================
Chapter 7, Sections 7.2 and 7.3. Produces Tables 7.1 and 7.2, and the cell
counts of the In the DataLab box.

On the primary dataset: the five strata of the logistic score, what each
contributes to the estimate of the ATT, and the demonstration that
subclassification is a weighted comparison whose weights change in steps.
The truth file is read only to score the final estimate.

    python ch07/07_01_form_strata.py
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common7 import (cli, banner, score, strata, subclass, stratum_weights,
                      att_weights, kish, pct)
import numpy as np


def table_7_1(ps, D, y):
    """Subclassification against the same estimate written as weights."""
    rows = []
    for K in (5, 20, 100):
        est, _, _ = subclass(ps, D, y, K, "ATT")
        w = stratum_weights(ps, D, K, "ATT")                  # Fragment 7.2
        wt = y[D == 1].mean() - np.average(y[D == 0], weights=w[D == 0])
        rows.append((f"{K} strata", est, wt, abs(est - wt), kish(w[D == 0])))
    wo = att_weights(ps, D)
    rows.append(("Odds weighting (Chapter 6)", np.nan,
                 y[D == 1].mean() - np.average(y[D == 0], weights=wo[D == 0]),
                 np.nan, kish(wo[D == 0])))
    return rows


def table_7_2(ps, D, y, tau, K=5):
    s = strata(ps, D, K)
    rows = []
    for k in range(K):
        m = s == k
        t, c = m & (D == 1), m & (D == 0)
        rows.append(dict(stratum=k + 1, lo=ps[m].min(), hi=ps[m].max(),
                         n_t=int(t.sum()), n_c=int(c.sum()),
                         y_t=y[t].mean(), y_c=y[c].mean(),
                         diff=y[t].mean() - y[c].mean(), share=t.sum() / D.sum(),
                         true_att=tau[t].mean()))
    return rows


def cell_sizes(ps, D, K):
    """Smallest stratum-by-condition cell, and how many cells hold under 20."""
    s = strata(ps, D, K)
    cells = np.r_[np.bincount(s[D == 1], minlength=K), np.bincount(s[D == 0], minlength=K)]
    return int(cells.min()), int((cells < 20).sum())


def main():
    a = cli(__doc__)
    sc = score(a.datadir, "logit", with_truth=True)
    D, ps, y, tau = sc["D"], sc["ps"], sc["y"], sc["tau"]

    banner("Table 7.1 - subclassification is weighting in steps, ATT")
    print(f"  {'':28s} {'Subclass':>10s} {'Weighted':>10s} {'Difference':>12s} {'Eff. controls':>14s}")
    for lab, est, wt, diff, ess in table_7_1(ps, D, y):
        e = "-" if np.isnan(est) else f"${est:,.0f}"
        d = "-" if np.isnan(diff) else f"{diff:.1e}"
        print(f"  {lab:28s} {e:>10s} {'$' + format(wt, ',.0f'):>10s} {d:>12s} {ess:>14,.0f}")
    print(f"  controls: {int((D == 0).sum()):,}")

    # Fragment 7.1: five strata, and the estimate built from them
    banner("Table 7.2 - five strata on the logistic score, primary dataset")
    rows = table_7_2(ps, D, y, tau)
    print(f"  {'':3s} {'Score range':>15s} {'Treated':>8s} {'Controls':>9s} "
          f"{'Treated mean':>13s} {'Control mean':>13s} {'Difference':>11s} {'Weight':>7s} {'True ATT':>9s}")
    for r in rows:
        print(f"  {r['stratum']:<3d} {r['lo']:.3f} to {r['hi']:.3f} {r['n_t']:8,d} {r['n_c']:9,d} "
              f"{r['y_t']:13,.0f} {r['y_c']:13,.0f} {r['diff']:+11,.0f} {r['share']:7.3f} "
              f"{r['true_att']:9,.0f}")
    est = sum(r["diff"] * r["share"] for r in rows)
    truth = tau[D == 1].mean()
    naive = y[D == 1].mean() - y[D == 0].mean()
    print(f"\n  subclassification ATT ${est:,.0f} against a true ATT of ${truth:,.0f} "
          f"({pct(est, truth):+.1f}%)")
    print(f"  naive difference in means ${naive:,.0f} ({pct(naive, truth):+.1f}%)")
    for K in (20, 100):
        e, _, _ = subclass(ps, D, y, K, "ATT")
        print(f"  with {K} strata ${e:,.0f} ({pct(e, truth):+.1f}%)")

    banner("In the DataLab - the smallest cells a stratum table would release")
    for K in (5, 20, 50, 100, 200):
        smallest, under = cell_sizes(ps, D, K)
        print(f"  {K:3d} strata: smallest cell {smallest:5,d}; "
              f"{under:3d} of {2 * K} cells hold fewer than 20 persons")


if __name__ == "__main__":
    main()
