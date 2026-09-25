#!/usr/bin/env python3
"""
Script 7.2 — How many strata, across six draws
===============================================
Chapter 7, Sections 7.4 to 7.8 and 7.10. Produces Tables 7.3, 7.4, 7.5 and
7.7, and the figures quoted in the box of Section 7.7.

Subclassification with 2 to 100 strata, with and without regression inside
each stratum and with and without Chapter 4's trimming rule, on the logistic
score and the six draws of Chapters 5 and 6. Each estimate is scored against
the truth for the persons it describes. The matching and weighting estimates
of Table 7.7 are recomputed with Chapters 5 and 6's own functions rather than
copied.

It generates its own draws and ignores --datadir.

    python ch07/07_02_compare_strata.py
    python ch07/07_02_compare_strata.py --quick
"""
import sys, tempfile
import atexit, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _common7 import (cli, banner, score, trimming_rules, TRIM_RULE, KS, make_draw,
                      subclass, stratum_weights, stratified_smd, ate_weights,
                      att_weights, ate_normalised, att_odds, outcome_design,
                      outcome_fits, att_dr, nn_match, mahalanobis_match, matched_att,
                      regression_on_score, overlap_truth, spline_on_score, pct)
import numpy as np, pandas as pd

SEEDS = [20260808, 20260809, 20260810, 20260811, 20260812, 20260813]


def one_draw(seed, tmp):
    out = make_draw(seed, tmp)
    sc = score(out, "logit", with_truth=True)
    E, X, D, ps, y, tau = sc["E"], sc["X"], sc["D"], sc["ps"], sc["y"], sc["tau"]
    Q = outcome_design(E, X, with_occupation=True).values.astype(float)
    keep = trimming_rules(ps, D)[TRIM_RULE]
    rows = []
    for trimmed in (False, True):
        k = keep if trimmed else np.ones(len(D), bool)
        p, d, yy, t, q, x = ps[k], D[k], y[k], tau[k], Q[k], X[k]
        truth = {"ATE": t.mean(), "ATT": t[d == 1].mean(), "ATO": overlap_truth(p, t)}

        def put(estimand, estimator, est, K=np.nan, **extra):
            rows.append(dict(seed=seed, trimmed=trimmed, n=int(k.sum()), estimand=estimand,
                             estimator=estimator, K=K, est=est, truth=truth[estimand],
                             bias=pct(est, truth[estimand]), **extra))

        naive = yy[d == 1].mean() - yy[d == 0].mean()
        put("ATT", "naive", naive)
        put("ATE", "naive", naive)
        put("ATT", "odds weighting", att_odds(d, yy, att_weights(p, d)))
        put("ATE", "normalised IPW", ate_normalised(d, yy, ate_weights(p, d)))
        for K in KS:
            for est in ("ATT", "ATE"):
                e, se, dropped = subclass(p, d, yy, K, est)
                w = stratum_weights(p, d, K, est)
                wt = (np.average(yy[d == 1], weights=w[d == 1])
                      - np.average(yy[d == 0], weights=w[d == 0]))
                put(est, "subclassification", e, K, se=se, dropped=dropped,
                    weighted_gap=abs(wt - e))
            if K in (5, 10, 20):
                for est in ("ATT", "ATE"):
                    e, _, _ = subclass(p, d, yy, K, est, Q=q)      # Fragment 7.3
                    put(est, "subclassification + regression", e, K)
                    smd = np.abs(stratified_smd(x, p, d, K, est))
                    put(est, "balance", np.nan, K, max_smd=smd.max(),
                        over_005=int((smd > 0.05).sum()), over_01=int((smd > 0.1).sum()))
                e, _, _ = subclass(p, d, yy, K, "ATT", on="treated")
                put("ATT", "subclassification, treated quantiles", e, K)
        # Section 7.7's box: the regression on the score, against three estimands
        b = regression_on_score(p, d, yy)
        for est in ("ATE", "ATT", "ATO"):
            put(est, "regression on the score", b)
        put("ATO", "overlap weighting", ate_normalised(d, yy, np.where(d == 1, 1 - p, p)))
        # Table 7.8: every chapter's principal ATT estimators on the same draws
        mt, mc = nn_match(p, d, 0.1, False, 1)
        put("ATT", "PS matching", (yy[mt] - yy[mc]).mean(), pairs=len(mt),
            truth_matched=t[mt].mean())
        mt, mc = mahalanobis_match(x.reset_index(drop=True), d, p, 0.1)
        put("ATT", "Mahalanobis matching", (yy[mt] - yy[mc]).mean(), pairs=len(mt),
            truth_matched=t[mt].mean())
        m1, m0 = outcome_fits(pd.DataFrame(q), d, yy)
        put("ATT", "doubly robust", att_dr(p, d, yy, m0)[0])
        put("ATT", "spline on the score + covariates", spline_on_score(p, d, yy, q)[1])
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
    t.to_csv(a.outdir / "strata_results.csv", index=False)
    report(t, len(seeds))


def cell(t, trimmed, estimand, estimator, K=None, col="bias"):
    q = t[(t.trimmed == trimmed) & (t.estimand == estimand) & (t.estimator == estimator)]
    if K is not None:
        q = q[q.K == K]
    return q[col].mean(), q[col].std()


def matched_bias(t, trimmed, estimator):
    """Matching is scored against the true ATT of the treated it matched."""
    q = t[(t.trimmed == trimmed) & (t.estimator == estimator)]
    b = 100 * (q.est - q.truth_matched) / q.truth_matched
    return b.mean(), b.std()


def report(t, nd):
    banner(f"Table 7.3 - bias by the number of strata, {nd} draw(s)")
    print(f"  {'':24s} {'ATT':>14s} {'ATT trim':>9s} {'ATE':>14s} {'ATE trim':>9s}")
    rows = [(f"{K} strata", "subclassification", K) for K in KS]
    rows += [("Odds weighting", "odds weighting", None), ("Normalised IPW", "normalised IPW", None),
             ("Naive difference", "naive", None)]
    for lab, est, K in rows:
        out = []
        for estimand in ("ATT", "ATE"):
            if (estimand == "ATT" and est == "normalised IPW") or (estimand == "ATE" and est == "odds weighting"):
                out += ["", ""]
                continue
            m, s = cell(t, False, estimand, est, K)
            mt_, _ = cell(t, True, estimand, est, K)
            out += [f"{m:+.1f}% ({s:.1f})", f"{mt_:+.1f}%"]
        print(f"  {lab:24s} {out[0]:>14s} {out[1]:>9s} {out[2]:>14s} {out[3]:>9s}")

    for K in (5, 10, 20):
        a_, _ = cell(t, False, "ATT", "subclassification, treated quantiles", K)
        b_, _ = cell(t, False, "ATT", "subclassification", K)
        print(f"  strata cut at the treated persons' quantiles, {K} strata: ATT {a_:+.1f}% "
              f"(everyone's quantiles {b_:+.1f}%)")
    sub = t[(t.estimator == "subclassification") & (~t.trimmed)]
    print(f"\n  largest gap between subclassification and its weights: "
          f"${t[t.estimator == 'subclassification'].weighted_gap.max():.1e}")
    print(f"  strata dropped for lacking a group: {int(t.dropped.max())}")
    for estimand in ("ATT", "ATE"):
        w = sub[sub.estimand == estimand].pivot(index="seed", columns="K", values="bias")
        naive = t[(t.estimator == "naive") & (~t.trimmed) & (t.estimand == estimand)].set_index("seed").bias
        ref = t[(t.estimator == ("odds weighting" if estimand == "ATT" else "normalised IPW"))
                & (~t.trimmed) & (t.estimand == estimand)].set_index("seed").bias
        d = w[20] - w[5]
        print(f"\n  {estimand}: five to twenty strata moves the estimate by {d.mean():+.1f} points "
              f"(sd {d.std():.2f}; smallest {d.abs().min():.1f}, largest {d.abs().max():.1f})")
        print(f"  {estimand}: twenty to a hundred strata {(w[100] - w[20]).mean():+.1f} points; "
              f"draw-to-draw sd with twenty strata {w[20].std():.1f}")
        print(f"  {estimand}: five strata remove {100 * (1 - (w[5] / naive)).mean():.0f}% of the naive bias, "
              f"twenty remove {100 * (1 - (w[20] / naive)).mean():.0f}%; five remove "
              f"{100 * ((naive - w[5]) / (naive - ref)).mean():.0f}% of what weighting removes")

    for estimand in ("ATT", "ATE"):
        banner(f"Table 7.4 - balance after stratification, {estimand} weighting, {nd} draw(s)")
        print(f"  {'':10s} {'Largest SMD':>12s} {'Over 0.05':>10s} {'Over 0.1':>9s} {'Bias':>8s}")
        for K in (5, 10, 20):
            ms, _ = cell(t, False, estimand, "balance", K, "max_smd")
            o5, _ = cell(t, False, estimand, "balance", K, "over_005")
            o1, _ = cell(t, False, estimand, "balance", K, "over_01")
            b, _ = cell(t, False, estimand, "subclassification", K)
            print(f"  {K:2d} strata  {ms:12.3f} {o5:10.1f} {o1:9.1f} {b:+7.1f}%")

    banner(f"Table 7.5 - regression within strata, {nd} draw(s)")
    print(f"  {'':10s} {'ATT':>14s} {'ATT trim':>9s} {'ATE':>14s} {'ATE trim':>9s}   plain ATT")
    for K in (5, 10, 20):
        out = []
        for estimand in ("ATT", "ATE"):
            m, s = cell(t, False, estimand, "subclassification + regression", K)
            mt_, _ = cell(t, True, estimand, "subclassification + regression", K)
            out += [f"{m:+.1f}% ({s:.1f})", f"{mt_:+.1f}%"]
        pl, _ = cell(t, False, "ATT", "subclassification", K)
        print(f"  {K:2d} strata  {out[0]:>14s} {out[1]:>9s} {out[2]:>14s} {out[3]:>9s}   {pl:+.1f}%")
    r = t[(t.estimator == "subclassification + regression") & (~t.trimmed)]
    for estimand in ("ATT", "ATE"):
        w = r[r.estimand == estimand].pivot(index="seed", columns="K", values="bias")
        print(f"  {estimand}: mean within-draw spread across 5, 10 and 20 strata "
              f"{(w.max(axis=1) - w.min(axis=1)).mean():.2f} points")

    banner(f"Section 7.7 box - regression on the score, {nd} draw(s)")
    for trimmed in (False, True):
        tr = "trimmed" if trimmed else "untrimmed"
        q = t[(t.estimator == "regression on the score") & (t.trimmed == trimmed)]
        tru = {e: q[q.estimand == e].truth.mean() for e in ("ATE", "ATO", "ATT")}
        bias = {e: q[q.estimand == e].bias.mean() for e in ("ATE", "ATO", "ATT")}
        sd = {e: q[q.estimand == e].bias.std() for e in ("ATE", "ATO", "ATT")}
        ow, _ = cell(t, trimmed, "ATO", "overlap weighting")
        print(f"  {tr}: estimate ${q.est.mean():,.0f}; truths ATE ${tru['ATE']:,.0f}, "
              f"overlap ${tru['ATO']:,.0f}, ATT ${tru['ATT']:,.0f}")
        print(f"    bias against the ATE {bias['ATE']:+.1f}% (sd {sd['ATE']:.1f}), "
              f"the overlap effect {bias['ATO']:+.1f}% (sd {sd['ATO']:.1f}), "
              f"the ATT {bias['ATT']:+.1f}%; overlap weighting {ow:+.1f}%")

    banner(f"Table 7.8 - the ATT across Chapters 5 to 7, {nd} draw(s)")
    print(f"  {'':40s} {'Untrimmed':>16s} {'Trimmed':>9s}")
    for lab, est, K in [("PS matching, caliper 0.1 (Ch 5)", "PS matching", None),
                        ("Mahalanobis within a caliper (Ch 5)", "Mahalanobis matching", None),
                        ("Odds weighting (Ch 6)", "odds weighting", None),
                        ("Doubly robust (Ch 6)", "doubly robust", None),
                        ("Subclassification, 20 strata", "subclassification", 20),
                        ("... with regression within strata", "subclassification + regression", 20),
                        ("Spline on the score + covariates", "spline on the score + covariates", None)]:
        if "matching" in est:
            m, s = matched_bias(t, False, est)
            mt_, _ = matched_bias(t, True, est)
        else:
            m, s = cell(t, False, "ATT", est, K)
            mt_, _ = cell(t, True, "ATT", est, K)
        print(f"  {lab:40s} {m:+8.1f}% ({s:.1f}) {mt_:+8.1f}%")

    banner(f"Section 7.4 - naive standard errors against the spread, {nd} draw(s)")
    for trimmed in (False, True):
        for estimand in ("ATT", "ATE"):
            for K in (5, 10, 20):
                q = t[(t.estimator == "subclassification") & (t.trimmed == trimmed)
                      & (t.estimand == estimand) & (t.K == K)]
                ratio = q.se.mean() / (q.est - q.truth).std()
                print(f"  {'trimmed' if trimmed else 'untrimmed':9s} {estimand} {K:2d} strata: "
                      f"se ${q.se.mean():,.0f}, spread ${(q.est - q.truth).std():,.0f}, ratio {ratio:.2f}")


if __name__ == "__main__":
    main()
