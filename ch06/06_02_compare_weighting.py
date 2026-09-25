#!/usr/bin/env python3
"""
Script 6.2 — Weighting across six draws
========================================
Chapter 6, Sections 6.4 to 6.10. Produces Tables 6.2 to 6.6 and 6.8, and
Figures 6.1 and 6.2.

Every weighting estimator the chapter discusses, on both scores of Chapter 3,
with and without Chapter 4's trimming rule, scored against the truth for the
persons each one describes. The draws are the six Chapter 5 used, so the
matching results here are Chapter 5's, recomputed rather than copied.

It generates its own draws and ignores --datadir.

    python ch06/06_02_compare_weighting.py
    python ch06/06_02_compare_weighting.py --quick
"""
import sys, subprocess, tempfile
import atexit, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _common6 import (cli, banner, score, trimming_rules, nn_match, mahalanobis_match,
                      TRIM_RULE, REPO, ate_weights, stabilised_weights, att_weights,
                      kish, cap, ate_unnormalised, ate_normalised, att_odds, ate_se,
                      att_se, outcome_design, outcome_fits, ate_dr, att_dr,
                      att_regression, pct)
import numpy as np, pandas as pd

SEEDS = [20260808, 20260809, 20260810, 20260811, 20260812, 20260813]
CAPS = [100, 99.9, 99.5, 99, 97.5, 95, 90]


def _matched_regression(X, D, y, mt, mc):
    """Section 5.12's regression adjustment on a matched sample."""
    from sklearn.linear_model import LinearRegression
    Xs = np.vstack([X.iloc[mt].values, X.iloc[mc].values])
    ys = np.r_[y[mt], y[mc]]
    ds = np.r_[np.ones(len(mt)), np.zeros(len(mc))]
    return LinearRegression().fit(np.c_[ds, Xs], ys).coef_[0]


def one_draw(seed, tmp):
    out = tmp / f"d{seed}"
    subprocess.run([sys.executable, str(REPO / "make_data.py"), "--seed", str(seed),
                    "--n", "50000", "--outdir", str(out), "--quiet"], check=True)
    for s in ("ch02/02_05_link_modules.py", "ch02/02_06_reshape_panel.py"):
        subprocess.run([sys.executable, str(REPO / s), "--datadir", str(out)],
                       check=True, capture_output=True)
    rows = []

    def put(**k):
        k.setdefault("se", np.nan)
        k["bias"] = pct(k["est"], k["truth"])
        rows.append(dict(seed=seed, **k))

    for sc_name in ("logit", "gbm"):
        sc = score(out, sc_name, with_truth=True)
        E, X, D, ps, y, tau = sc["E"], sc["X"], sc["D"], sc["ps"], sc["y"], sc["tau"]
        Q = outcome_design(E, X, with_occupation=True)
        Q0 = outcome_design(E, X, with_occupation=False)
        keep_rule = trimming_rules(ps, D)[TRIM_RULE]
        for trimmed in (False, True):
            k = keep_rule if trimmed else np.ones(len(D), bool)
            p, d, yy, t = ps[k], D[k], y[k], tau[k]
            ate_t, att_t = t.mean(), t[d == 1].mean()
            base = dict(score=sc_name, trimmed=trimmed, n=int(k.sum()),
                        n_t=int(d.sum()), n_c=int((d == 0).sum()))
            w, sw, wo = ate_weights(p, d), stabilised_weights(p, d), att_weights(p, d)

            # Section 6.4: normalisation and stabilisation
            put(**base, estimand="ATE", estimator="unnormalised",
                est=ate_unnormalised(p, d, yy), truth=ate_t)
            put(**base, estimand="ATE", estimator="normalised",
                est=ate_normalised(d, yy, w), truth=ate_t, se=ate_se(p, d, yy))
            put(**base, estimand="ATE", estimator="stabilised",
                est=ate_normalised(d, yy, sw), truth=ate_t)
            put(**base, estimand="ATT", estimator="odds",
                est=att_odds(d, yy, wo), truth=att_t, se=att_se(p, d, yy))

            # Section 6.6: capping the weights instead of trimming the sample
            for q in CAPS[1:]:
                put(**base, estimand="ATE", estimator=f"cap {q}",
                    est=ate_normalised(d, yy, cap(w, np.ones(len(d), bool), q)), truth=ate_t)
                put(**base, estimand="ATT", estimator=f"cap {q}",
                    est=att_odds(d, yy, cap(wo, d == 0, q)), truth=att_t)

            # Section 6.8: doubly robust, with and without occupation_group
            for lab, QQ in (("", Q), (" no occupation", Q0)):
                m1, m0 = outcome_fits(QQ[k], d, yy)
                e, s_ = ate_dr(p, d, yy, m1, m0)
                put(**base, estimand="ATE", estimator="doubly robust" + lab,
                    est=e, truth=ate_t, se=s_)
                e, s_ = att_dr(p, d, yy, m0)
                put(**base, estimand="ATT", estimator="doubly robust" + lab,
                    est=e, truth=att_t, se=s_)
                put(**base, estimand="ATE", estimator="regression" + lab,
                    est=(m1 - m0).mean(), truth=ate_t)
                put(**base, estimand="ATT", estimator="regression" + lab,
                    est=att_regression(d, yy, m0), truth=att_t)

            # weight diagnostics, for Table 6.1's companion rows and Section 6.6
            rows.append(dict(seed=seed, **base, estimand="diag", estimator="weights",
                             est=np.nan, truth=np.nan, bias=np.nan, se=np.nan,
                             max_w=w.max(), max_sw=sw.max(),
                             max_odds=wo[d == 0].max(),
                             ess_ate_t=kish(w[d == 1]), ess_ate_c=kish(w[d == 0]),
                             ess_att_c=kish(wo[d == 0])))

        if sc_name == "logit":
            # Section 6.9: the matching of Chapter 5, on the same draw
            att_all = tau[D == 1].mean()
            mt, mc = nn_match(ps, D, 0.1, False, 1)
            put(score="logit", trimmed=False, estimand="ATT", estimator="PS matching",
                est=(y[mt] - y[mc]).mean(), truth=tau[mt].mean())
            put(score="logit", trimmed=False, estimand="ATT",
                estimator="PS matching + regression",
                est=_matched_regression(X, D, y, mt, mc), truth=tau[mt].mean())
            mt, mc = mahalanobis_match(X, D, ps, 0.1)
            put(score="logit", trimmed=False, estimand="ATT", estimator="Mahalanobis matching",
                est=(y[mt] - y[mc]).mean(), truth=tau[mt].mean())

            # Section 6.7: the near-instrument, from the weighting side
            sys.path.insert(0, str(REPO / "ch03"))
            from _common3 import fit_propensity
            MO = pd.get_dummies(E["mutual_obligation_status"], prefix="mo",
                                drop_first=True).astype(float).set_index(X.index)
            ps_mo = fit_propensity(pd.concat([X, MO], axis=1), D, "logit")
            wo_mo = att_weights(ps_mo, D)
            put(score="logit+mo", trimmed=False, estimand="ATT", estimator="odds",
                est=att_odds(D, y, wo_mo), truth=att_all, se=att_se(ps_mo, D, y))
            rows.append(dict(seed=seed, score="logit+mo", trimmed=False, estimand="diag",
                             estimator="weights", est=np.nan, truth=np.nan, bias=np.nan,
                             se=np.nan, max_odds=wo_mo[D == 0].max(),
                             ess_att_c=kish(wo_mo[D == 0])))
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
    t.to_csv(a.outdir / "weighting_results.csv", index=False)
    report(t, len(seeds))
    if a.quick:
        print("\n  --quick: skipping Figures 6.1 and 6.2, which need all six draws.")
        return
    _figure_capping(t, a.outdir)
    _figure_att(t, a.outdir)


def cell(t, score, trimmed, estimand, estimator):
    q = t[(t.score == score) & (t.trimmed == trimmed) & (t.estimand == estimand)
          & (t.estimator == estimator)]
    # sd of the error (estimate less truth), in dollars: the truth itself moves
    # a little from draw to draw, and a standard error is about the error.
    return q.bias.mean(), q.bias.std(), (q.est - q.truth).std(), q.se.mean()


def report(t, nd):
    banner(f"Table 6.2 - normalisation and stabilisation, ATE, {nd} draw(s)")
    print(f"  {'Estimator':16s} {'logit':>9s} {'boosted':>9s} {'logit trim':>11s} {'boost trim':>11s}")
    for e in ("unnormalised", "normalised", "stabilised"):
        v = [cell(t, s, tr, "ATE", e)[0] for tr in (False, True) for s in ("logit", "gbm")]
        print(f"  {e:16s} {v[0]:+8.1f}% {v[1]:+8.1f}% {v[2]:+10.1f}% {v[3]:+10.1f}%")
    n = t[(t.estimand == "ATE") & (t.estimator == "normalised")].est.values
    s_ = t[(t.estimand == "ATE") & (t.estimator == "stabilised")].est.values
    print(f"\n  largest difference, normalised against stabilised: ${np.abs(n - s_).max():.2e}")

    banner(f"Table 6.3 - weighting across {nd} draw(s): bias (sd)")
    print(f"  {'':22s} {'ATE':>16s} {'ATT':>16s}")
    for s in ("logit", "gbm"):
        for tr in (False, True):
            a_ = cell(t, s, tr, "ATE", "normalised")
            b_ = cell(t, s, tr, "ATT", "odds")
            lab = f"{s}{', trimmed' if tr else ''}"
            print(f"  {lab:22s} {a_[0]:+7.1f}% ({a_[1]:4.1f}) {b_[0]:+7.1f}% ({b_[1]:4.1f})")

    banner("Table 6.4 - capping the weights against trimming the sample, logistic score")
    print(f"  {'':22s} {'ATE bias':>10s} {'ATT bias':>10s}")
    for q in ("normalised/odds", *[f"cap {c}" for c in CAPS[1:]]):
        if q == "normalised/odds":
            a_, b_ = cell(t, "logit", False, "ATE", "normalised"), cell(t, "logit", False, "ATT", "odds")
            lab = "no cap"
        else:
            a_, b_ = cell(t, "logit", False, "ATE", q), cell(t, "logit", False, "ATT", q)
            lab = f"capped at {q[4:]}th pct"
        print(f"  {lab:22s} {a_[0]:+9.1f}% {b_[0]:+9.1f}%")
    a_, b_ = cell(t, "logit", True, "ATE", "normalised"), cell(t, "logit", True, "ATT", "odds")
    print(f"  {'trimmed (Chapter 4)':22s} {a_[0]:+9.1f}% {b_[0]:+9.1f}%")

    banner("Table 6.5 - the doubly robust estimator and its two ingredients")
    print(f"  {'':34s} {'ATE bias':>9s} {'sd':>5s} {'ATT bias':>9s} {'sd':>5s}")
    for sc_, lab, ea, eb in (("logit", "weighting alone", "normalised", "odds"),
                             ("logit", "outcome regression alone", "regression", "regression"),
                             ("logit", "doubly robust", "doubly robust", "doubly robust"),
                             ("gbm", "doubly robust, boosted score", "doubly robust",
                              "doubly robust")):
        for tr in (False, True):
            a_, b_ = cell(t, sc_, tr, "ATE", ea), cell(t, sc_, tr, "ATT", eb)
            print(f"  {lab + (', trimmed' if tr else ''):34s} {a_[0]:+8.1f}% {a_[1]:5.1f} "
                  f"{b_[0]:+8.1f}% {b_[1]:5.1f}")

    # Section 6.8: what occupation_group buys, as Table 2.2 measured it
    for est in ("ATE", "ATT"):
        a_ = t[(t.score == "logit") & (~t.trimmed) & (t.estimand == est)
               & (t.estimator == "doubly robust")].set_index("seed").se
        b_ = t[(t.score == "logit") & (~t.trimmed) & (t.estimand == est)
               & (t.estimator == "doubly robust no occupation")].set_index("seed").se
        r = a_ / b_
        print(f"  occupation_group, doubly robust {est}: standard error ratio "
              f"{r.mean():.3f}, smaller in {int((r < 1).sum())} of {len(r)} draws")

    banner("Table 6.6 - weighting against matching for the ATT, logistic score")
    for e in ("odds", "doubly robust", "PS matching", "PS matching + regression",
              "Mahalanobis matching"):
        b_ = cell(t, "logit", False, "ATT", e)
        print(f"  {e:28s} {b_[0]:+7.1f}%  sd {b_[1]:4.1f}")

    banner("Section 6.7 - the near-instrument, from the weighting side")
    w0 = t[(t.score == "logit") & (~t.trimmed) & (t.estimand == "diag")]
    w1 = t[(t.score == "logit+mo") & (t.estimand == "diag")]
    b0, b1 = cell(t, "logit", False, "ATT", "odds"), cell(t, "logit+mo", False, "ATT", "odds")
    print(f"  {'':30s} {'without':>10s} {'with':>10s}")
    print(f"  {'odds-weighted ATT bias':30s} {b0[0]:+9.1f}% {b1[0]:+9.1f}%")
    print(f"  {'sd across draws':30s} {b0[1]:10.1f} {b1[1]:10.1f}")
    print(f"  {'naive standard error':30s} {b0[3]:10,.0f} {b1[3]:10,.0f}")
    print(f"  {'effective control sample':30s} {w0.ess_att_c.mean():10,.0f} {w1.ess_att_c.mean():10,.0f}")
    print(f"  {'largest control odds weight':30s} {w0.max_odds.mean():10.1f} {w1.max_odds.mean():10.1f}")

    banner("Table 6.8 - naive standard errors against the spread across draws")
    for s, e, lab in (("logit", "normalised", "IPW, ATE"), ("logit", "odds", "odds, ATT"),
                      ("logit", "doubly robust", "doubly robust, ATE"),
                      ("logit", "doubly robust", "doubly robust, ATT")):
        est = "ATE" if "ATE" in lab else "ATT"
        a_ = cell(t, s, False, est, e)
        print(f"  {lab:22s} naive SE ${a_[3]:6,.0f}   sd of the error ${a_[2]:6,.0f}"
              f"   ratio {a_[3] / a_[2]:.2f}")


def _style():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.linewidth": 0.8,
                         "axes.labelsize": 8.5, "xtick.labelsize": 7.5,
                         "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
                         "legend.frameon": False, "savefig.dpi": 300,
                         "savefig.bbox": "tight", "savefig.facecolor": "white"})
    return plt


def _figure_capping(t, outdir):
    plt = _style()
    fig, axes = plt.subplots(1, 2, figsize=(6.9, 3.0), sharey=False)
    xs = list(range(len(CAPS)))
    for ax, (estimand, base), letter in zip(axes, (("ATE", "normalised"), ("ATT", "odds")), "ab"):
        for s, mk, ls in (("logit", "o", "-"), ("gbm", "s", "--")):
            v = [cell(t, s, False, estimand, base if c == 100 else f"cap {c}")[0] for c in CAPS]
            ax.plot(xs, v, marker=mk, markersize=4.5, markerfacecolor="white",
                    markeredgecolor="black", color="black", linewidth=0.8, linestyle=ls,
                    label="logistic score" if s == "logit" else "boosted score")
            tr = cell(t, s, True, estimand, base)[0]
            ax.axhline(tr, color="black", linewidth=0.7, linestyle=(0, (1, 2)))
            ax.text(len(CAPS) - 1, tr, f" trimmed, {'logistic' if s == 'logit' else 'boosted'}",
                    fontsize=6.5, va="bottom", ha="right")
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_xticks(xs)
        ax.set_xticklabels(["none"] + [f"{c:g}" for c in CAPS[1:]])
        ax.set_xlabel("Weights capped at percentile")
        ax.set_title(f"{estimand}, {'inverse probability' if estimand == 'ATE' else 'odds'} weights",
                     fontsize=9)
        ax.text(-0.02, 1.07, f"({letter})", transform=ax.transAxes, fontsize=10,
                fontweight="bold", va="bottom", ha="right")
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axes[0].set_ylabel("Bias, mean of six draws (%)")
    axes[1].legend(loc="lower left")
    fig.subplots_adjust(wspace=0.28)
    for ext in ("tif", "png"):
        fig.savefig(outdir / f"figure_6_1_capping.{ext}")
    print(f"\n  wrote figure_6_1_capping.tif to {outdir}")


ATT_SHOWN = [("odds", "odds\nweighting"), ("doubly robust", "doubly\nrobust"),
             ("PS matching", "propensity score\nmatching"),
             ("Mahalanobis matching", "Mahalanobis\nmatching"),
             ("regression", "regression\nalone")]


def _figure_att(t, outdir):
    plt = _style()
    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    seeds = sorted(t.seed.unique())
    for j, (e, lab) in enumerate(ATT_SHOWN):
        q = t[(t.score == "logit") & (~t.trimmed) & (t.estimand == "ATT") & (t.estimator == e)]
        v = q.set_index("seed").loc[seeds, "bias"].values
        ax.scatter(np.full(len(v), j), v, s=16, facecolors="white", edgecolors="black",
                   linewidths=0.8, zorder=3)
        ax.plot([j - 0.25, j + 0.25], [v.mean()] * 2, color="black", linewidth=1.4)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(range(len(ATT_SHOWN)))
    ax.set_xticklabels([lab for _, lab in ATT_SHOWN], fontsize=7.5)
    ax.set_ylabel("Bias of the ATT (%)")
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for ext in ("tif", "png"):
        fig.savefig(outdir / f"figure_6_2_att_estimators.{ext}")
    print(f"  wrote figure_6_2_att_estimators.tif to {outdir}")


if __name__ == "__main__":
    main()
