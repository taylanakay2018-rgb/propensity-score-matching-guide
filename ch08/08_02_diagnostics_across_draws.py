#!/usr/bin/env python3
"""
Script 8.2 — What the diagnostics can and cannot see, across six draws
======================================================================
Chapter 8, Sections 8.2 and 8.6 to 8.8. Produces Tables 8.4 to 8.7.

Seven adjusted samples per draw (propensity score matching, Mahalanobis
matching, odds weighting, and subclassification at 2, 5, 20 and 100 strata),
on both scores of Chapter 3 and the six draws of Chapters 5 to 7, for the
ATT. Every covariate diagnostic of Sections 8.3 to 8.5 is computed for each,
together with the secondary check of Section 8.8, and each sample's estimate
is scored against the truth for the treated persons it describes.

The truth file is read only to score the estimates and, in Section 8.2, to
confirm that the bias of each estimate equals the imbalance in the untreated
outcome. The secondary check itself uses the controls' outcomes only.

It generates its own draws and ignores --datadir.

    python ch08/08_02_diagnostics_across_draws.py
    python ch08/08_02_diagnostics_across_draws.py --quick
"""
import sys, tempfile
import atexit, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _common8 import (cli, banner, score, make_draw, adjusted_samples, diagnostics, summary,
                      constructed_terms, outcome_design, prognostic_score, predicted_bias,
                      wmean, pct)
import numpy as np, pandas as pd

SEEDS = [20260808, 20260809, 20260810, 20260811, 20260812, 20260813]
ORDER = ["Unadjusted", "Propensity score matching", "Mahalanobis matching", "Odds weighting",
         "Subclassification, 2 strata", "Subclassification, 5 strata",
         "Subclassification, 20 strata", "Subclassification, 100 strata"]


def one_draw(seed, tmp):
    out = make_draw(seed, tmp)
    rows = []
    for sc_name in ("logit", "gbm"):
        sc = score(out, sc_name, with_truth=True)
        E, X, D, ps, y, tau = sc["E"], sc["X"], sc["D"], sc["ps"], sc["y"], sc["tau"]
        y0 = y - tau * D                               # truth file: scoring only
        C = constructed_terms(X)
        Q = outcome_design(E, X, with_occupation=True).values.astype(float)
        prog = prognostic_score(Q, D, y, seed)         # Fragment 8.3: controls only
        for name, (wt, wc) in adjusted_samples(X, D, ps).items():
            est = wmean(y, wt) - wmean(y, wc)
            truth = wmean(tau, wt)
            r = dict(seed=seed, score=sc_name, sample=name, est=est, truth=truth,
                     bias=pct(est, truth), y0_gap=wmean(y0, wt) - wmean(y0, wc),
                     predicted=pct(truth + predicted_bias(prog, wt, wc), truth))
            r.update(summary(diagnostics(X, D, wt, wc, C=C)))
            rows.append(r)
    return rows


def main():
    a = cli(__doc__)
    seeds = SEEDS[:1] if a.quick else SEEDS
    tmp = Path(tempfile.mkdtemp())
    atexit.register(shutil.rmtree, tmp, ignore_errors=True)   # leave no draws behind
    rows = []
    for s in seeds:
        rows += one_draw(s, tmp)
        print(f"  draw {s} done", file=sys.stderr, flush=True)
    t = pd.DataFrame(rows)
    a.outdir.mkdir(parents=True, exist_ok=True)
    t.to_csv(a.outdir / "balance_results.csv", index=False)
    report(t, len(seeds))


def means(t, score):
    return t[t.score == score].groupby("sample").mean(numeric_only=True).reindex(ORDER)


def report(t, nd):
    gap = (t.est - t.truth - t.y0_gap).abs().max()
    banner(f"Section 8.2 - the bias is the imbalance in the untreated outcome, {nd} draw(s)")
    print(f"  largest difference between (estimate - truth) and the untreated-outcome gap, "
          f"over {len(t)} samples: ${gap:.1e}")

    banner(f"Table 8.4 - every diagnostic against the bias, logistic score, {nd} draw(s)")
    m = means(t, "logit")
    sd = t[t.score == "logit"].groupby("sample").bias.std().reindex(ORDER)
    print(f"  {'':32s} {'ATT bias':>14s} {'Largest':>8s} {'SMD':>6s} {'VR out':>7s} "
          f"{'Largest':>8s} {'Largest':>9s}")
    print(f"  {'':32s} {'':>14s} {'SMD':>8s} {'>0.05':>6s} {'':>7s} {'KS':>8s} {'term SMD':>9s}")
    for k, r in m.iterrows():
        print(f"  {k:32s} {r.bias:+7.1f}% ({sd[k]:4.1f}) {r.smd_max:8.3f} {r.smd_over_005:6.1f} "
              f"{r.vr_out:7.1f} {r.ks_max:8.3f} {r.con_max:9.3f}")
    adj = t[(t.score == "logit") & (t["sample"] != "Unadjusted")]
    ok = adj[(adj.smd_over_01 == 0) & (adj.con_over_01 == 0) & (adj.vr_out == 0)]
    print(f"\n  logistic-score samples passing every test (no SMD, term SMD over 0.1, no VR outside "
          f"0.8-1.25): {len(ok)} of {len(adj)}; their bias runs from {ok.bias.min():+.1f}% to "
          f"{ok.bias.max():+.1f}%")

    banner(f"Table 8.5 - propensity score matching less Mahalanobis matching, by draw")
    L = t[t.score == "logit"].set_index(["seed", "sample"])
    print(f"  {'Draw':10s} {'Bias':>8s} {'Largest SMD':>12s} {'Largest KS':>11s} "
          f"{'Largest term':>13s} {'Most extreme VR':>16s}")
    diffs = []
    for s in sorted(t.seed.unique()):
        p, q = L.loc[(s, "Propensity score matching")], L.loc[(s, "Mahalanobis matching")]
        d = dict(seed=s, bias=p.bias - q.bias, smd=p.smd_max - q.smd_max, ks=p.ks_max - q.ks_max,
                 con=p.con_max - q.con_max,
                 vr=abs(np.log(p.vr_extreme)) - abs(np.log(q.vr_extreme)),
                 predicted=p.predicted - q.predicted)
        diffs.append(d)
        print(f"  {s:<10d} {d['bias']:+8.1f} {d['smd']:+12.3f} {d['ks']:+11.3f} {d['con']:+13.3f} "
              f"{d['vr']:+16.3f}")
    d = pd.DataFrame(diffs)
    print(f"  the largest SMD says propensity score matching is the better balanced in "
          f"{int((d.smd < 0).sum())} of {len(d)} draws; it is the more biased in "
          f"{int((d.bias < 0).sum())} of {len(d)}")

    banner(f"Table 8.6 - the boosted score, {nd} draw(s)")
    g = t[t.score == "gbm"]
    print(f"  {'':32s} {'ATT bias':>9s} {'Largest':>8s} {'Draws failing':>14s} {'Draws failing':>14s}")
    print(f"  {'':32s} {'':>9s} {'SMD':>8s} {'0.1':>14s} {'0.05':>14s}")
    for k in ORDER[1:]:
        q = g[g["sample"] == k]
        print(f"  {k:32s} {q.bias.mean():+8.1f}% {q.smd_max.mean():8.3f} "
              f"{int((q.smd_over_01 > 0).sum()):>10d} of {len(q)} {int((q.smd_over_005 > 0).sum()):>10d} of {len(q)}")
    for k in ("Subclassification, 5 strata", "Subclassification, 20 strata", "Subclassification, 100 strata"):
        q = g[g["sample"] == k]
        print(f"  {k}: largest SMD {q.smd_max.min():.3f} to {q.smd_max.max():.3f}; "
              f"bias {q.bias.min():+.1f}% to {q.bias.max():+.1f}%")
    q = g[g["sample"] == "Propensity score matching"]
    print(f"  boosted score, propensity score matching: most common worst covariate "
          f"'{q.smd_worst.mode()[0]}'; bias {q.bias.min():+.1f}% to {q.bias.max():+.1f}%")

    banner(f"Table 8.7 - the secondary check: bias predicted by the prognostic score, {nd} draw(s)")
    print(f"  {'':32s} {'Logistic':>18s} {'Boosted':>18s}")
    print(f"  {'':32s} {'actual':>8s} {'predicted':>9s} {'actual':>8s} {'predicted':>9s}")
    ml, mg = means(t, "logit"), means(t, "gbm")
    for k in ORDER:
        print(f"  {k:32s} {ml.bias[k]:+7.1f}% {ml.predicted[k]:+8.1f}% {mg.bias[k]:+7.1f}% "
              f"{mg.predicted[k]:+8.1f}%")
    adj = t[t["sample"] != "Unadjusted"]
    passing = adj[adj.smd_over_01 == 0]
    cor = lambda d, c: float(np.corrcoef(d.bias, d[c])[0, 1])        # noqa: E731
    print(f"\n  correlation with the actual bias across {len(adj)} adjusted samples: "
          f"predicted {cor(adj, 'predicted'):.2f}, largest SMD {cor(adj, 'smd_max'):.2f}, "
          f"largest KS {cor(adj, 'ks_max'):.2f}")
    print(f"  among the {len(passing)} that pass the 0.1 test: predicted {cor(passing, 'predicted'):.2f}, "
          f"largest SMD {cor(passing, 'smd_max'):.2f}, largest KS {cor(passing, 'ks_max'):.2f}")
    print(f"  propensity score less Mahalanobis matching, predicted: "
          + ", ".join(f"{v:+.1f}" for v in d.predicted)
          + f"; mean {d.predicted.mean():+.1f} against an actual {d.bias.mean():+.1f}")
    res = adj.bias - adj.predicted
    print(f"  actual less predicted, all adjusted samples: mean {res.mean():+.1f} points "
          f"(sd {res.std():.1f})")


if __name__ == "__main__":
    main()
