#!/usr/bin/env python3
"""
Script 7.3 — Modelling the outcome on the score
================================================
Chapter 7, Section 7.9. Produces Table 7.6 and the table in the Trap box.

Outcome models fitted separately to each condition on a cubic spline of the
logistic score, with and without the covariates beside it, with and without
Chapter 4's trimming, on the six draws of Chapters 5 and 6. Each is fitted
twice: with the spline's knots at quantiles of the score, and with the
library default of knots spaced evenly across its range.

It generates its own draws and ignores --datadir.

    python ch07/07_03_spline_on_score.py
    python ch07/07_03_spline_on_score.py --quick
"""
import sys, tempfile
import atexit, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _common7 import (cli, banner, score, trimming_rules, TRIM_RULE, make_draw,
                      spline_on_score, outcome_design, pct)
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
        p, d, yy, t, q = ps[k], D[k], y[k], tau[k], Q[k]
        for knots in ("quantile", "uniform"):
            for cov in (False, True):
                ate, att = spline_on_score(p, d, yy, q if cov else None, knots)  # Fragment 7.4
                for estimand, est, truth in (("ATE", ate, t.mean()), ("ATT", att, t[d == 1].mean())):
                    rows.append(dict(seed=seed, trimmed=trimmed, knots=knots, covariates=cov,
                                     estimand=estimand, est=est, truth=truth,
                                     bias=pct(est, truth)))
    return rows, dict(seed=seed, **thinnest(ps, D))


def thinnest(ps, D):
    """Why evenly spaced knots fail: the emptiest interval between knots.

    The spline is fitted separately to each condition, so an interval of the
    score holding a handful of persons in one condition lets that condition's
    curve swing freely there, and the prediction for the other condition's
    persons in the same interval swings with it.
    """
    lp = np.log(ps / (1 - ps))
    res = {}
    for knots, edges in (("uniform", np.linspace(lp.min(), lp.max(), 10)),
                         ("quantile", np.quantile(lp, np.linspace(0, 1, 10)))):
        n1 = np.histogram(lp[D == 1], bins=edges)[0]
        n0 = np.histogram(lp[D == 0], bins=edges)[0]
        res[f"{knots}_t"], res[f"{knots}_c"] = int(n1.min()), int(n0.min())
    return res


def main():
    a = cli(__doc__)
    seeds = SEEDS[:1] if a.quick else SEEDS
    tmp = Path(tempfile.mkdtemp())
    atexit.register(shutil.rmtree, tmp, ignore_errors=True)   # leave no draws behind
    rows, thin = [], []
    for s in seeds:
        r, t_ = one_draw(s, tmp)
        rows += r
        thin.append(t_)
        print(f"  draw {s} done", file=sys.stderr, flush=True)
    t = pd.DataFrame(rows)
    a.outdir.mkdir(parents=True, exist_ok=True)
    t.to_csv(a.outdir / "spline_results.csv", index=False)
    pd.DataFrame(thin).to_csv(a.outdir / "spline_thinnest.csv", index=False)

    banner(f"Table 7.6 - outcome models on a spline of the score, {len(seeds)} draw(s)")
    print(f"  {'':40s} {'ATT':>18s} {'ATT trim':>10s} {'ATE':>18s} {'ATE trim':>10s}")
    for knots, klab in (("quantile", "knots at quantiles"), ("uniform", "knots evenly spaced")):
        for cov in (False, True):
            lab = f"Spline, {klab}" + (", + covariates" if cov else "")
            out = []
            for estimand in ("ATT", "ATE"):
                for trimmed in (False, True):
                    q = t[(t.knots == knots) & (t.covariates == cov) & (t.estimand == estimand)
                          & (t.trimmed == trimmed)]
                    out.append(f"{q.bias.mean():+.1f}%" + ("" if trimmed else f" ({q.bias.std():.1f})"))
            print(f"  {lab:40s} {out[0]:>18s} {out[1]:>10s} {out[2]:>18s} {out[3]:>10s}")

    banner("Table 7.7 - the thinnest interval between knots, untrimmed (Section 7.9)")
    print(f"  {'Draw':10s} {'Evenly spaced':>22s} {'At quantiles':>22s} {'Bias, evenly spaced':>22s}")
    print(f"  {'':10s} {'treated':>10s} {'controls':>11s} {'treated':>10s} {'controls':>11s} {'ATT':>10s} {'ATE':>11s}")
    for th in thin:
        q = t[(t.seed == th["seed"]) & (t.knots == "uniform") & (~t.covariates) & (~t.trimmed)]
        b = q.set_index("estimand").bias
        print(f"  {th['seed']:<10d} {th['uniform_t']:10,d} {th['uniform_c']:11,d} "
              f"{th['quantile_t']:10,d} {th['quantile_c']:11,d} {b['ATT']:+9.1f}% {b['ATE']:+10.1f}%")


if __name__ == "__main__":
    main()
