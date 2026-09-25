#!/usr/bin/env python3
"""
Script 10.2 — Sensitivity analysis and policy translation, primary dataset
===========================================================================
Chapter 10, Sections 10.3 and 10.4.1. Produces Tables 10.2, 10.3 and 10.4 and
Figure 10.1.

The two sensitivity analyses a researcher can run without the truth file:
Cinelli and Hazlett's omitted-variable analysis of the regression estimate,
benchmarked against observed covariates, and Rosenbaum's bound for matched
pairs. Each is then checked against the confounder that the truth file shows
was actually missing. The policy table converts the estimates into the
programme cost per participant at which the earnings gain would pay for it.

    python ch10/10_02_sensitivity.py
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common10 import (cli, banner, score, truth_file, outcome_design, regression_sensitivity,
                       adjusted, confounder_strength, benchmark, rosenbaum_gamma, within_pair_odds,
                       mahalanobis_match, nn_match, att_weights, att_odds, att_dr, outcome_fits,
                       sandwich_se, logit_design, paired_se)
import numpy as np, pandas as pd
from scipy.optimize import brentq

BENCHMARKS = [("edu", "highest education"), ("log_inc_2016", "log earnings 2016"),
              ("fn_2016", "fortnights on payment 2016")]
TAUS = [0, 2500, 5000]
DISCOUNT = 0.03


def main():
    a = cli(__doc__)
    sc = score(a.datadir, "logit", with_truth=True)
    E, X, D, ps, y, tau = sc["E"], sc["X"], sc["D"], sc["ps"], sc["y"], sc["tau"]
    T = truth_file(a.datadir).reindex(E.index)
    Qdf = outcome_design(E, X, with_occupation=True)
    Q, cols = Qdf.values.astype(float), list(Qdf.columns)
    u = T["u_employability"].values
    out = {}
    rec = {}                                     # every quoted number, for the audit

    banner("Table 10.2 - how strong would a confounder have to be? Primary dataset")
    r = regression_sensitivity(y, D, Q)
    print(f"  regression estimate ${r['est']:,.0f} (se ${r['se']:,.0f}); partial R2 of treatment "
          f"with earnings {r['r2_yd']:.4f}; robustness value {r['rv']:.3f}")
    q5 = 1 - 5000 / r["est"]
    rec.update(est=r["est"], se=r["se"], df=r["df"], r2_yd=r["r2_yd"], rv=r["rv"], rv_5000=r["rv_q"](q5))
    print(f"  robustness value for bringing the estimate down to $5,000: {r['rv_q'](q5):.3f}")
    print(f"\n  {'':42s} {'R2 with':>10s} {'R2 with':>10s} {'Largest':>10s}")
    print(f"  {'':42s} {'treatment':>10s} {'earnings':>10s} {'bias':>10s}")
    for k, lab in BENCHMARKS:
        dz, yz = benchmark(y, D, Q, cols, k)
        for mult in (1, 3):
            a_ = adjusted(r["est"], r["se"], r["df"], min(mult * dz, 0.99), min(mult * yz, 0.99))
            name = f"{'' if mult == 1 else f'{mult} x '}as strong as {lab}"
            print(f"  {name:42s} {mult * dz:10.4f} {mult * yz:10.4f} {r['est'] - a_:10,.0f}")
            out[f"bench_{k}_{mult}"] = (mult * dz, mult * yz, r["est"] - a_)
            rec.update({f"bench_{k}_{mult}_{n_}": v_ for n_, v_ in zip(("dz", "yz", "bias"), out[f"bench_{k}_{mult}"])})
    dz, yz = confounder_strength(y, D, Q, u)
    a_ = adjusted(r["est"], r["se"], r["df"], dz, yz)
    actual = np.linalg.lstsq(np.c_[np.ones(len(y)), D, Q, u], y, rcond=None)[0][1]
    print(f"  {'employability (truth file)':42s} {dz:10.4f} {yz:10.4f} {r['est'] - a_:10,.0f}")
    print(f"  refitting the regression with employability included gives ${actual:,.0f}, "
          f"a shift of {actual - r['est']:+,.0f}")
    out["u"] = (dz, yz, r["est"] - a_)
    # How many times as strong as education would a confounder have to be?
    dz1, yz1 = out["bench_edu_1"][:2]
    for target in (5000, 0):
        k = brentq(lambda k: adjusted(r["est"], r["se"], r["df"], k * dz1, min(k * yz1, 0.999)) - target,
                   0.01, 0.999 / max(dz1, yz1))
        print(f"  to bring the estimate down to ${target:,}, a confounder would have to be "
              f"{k:.1f} times as strong as education")
        rec[f"k_edu_{target}"] = k
    rec.update(u_dz=dz, u_yz=yz, u_bias=r["est"] - a_, u_refit=actual)

    banner("Table 10.3 - how much hidden bias would overturn the conclusion? Primary dataset")
    ht, hc = mahalanobis_match(X, D, ps, 0.1)
    mt, mc = nn_match(ps, D, 0.1, False, 1)
    lt = np.log(T["true_propensity"].values / (1 - T["true_propensity"].values))
    print(f"  {'':30s} " + " ".join(f"{'effect > $' + format(t_, ','):>15s}" for t_ in TAUS))
    for lab, (a1, b1) in (("Mahalanobis matching", (ht, hc)), ("PS matching", (mt, mc))):
        d = y[a1] - y[b1]
        g = [rosenbaum_gamma(d, t_) for t_ in TAUS]
        k_ = "maha" if lab.startswith("Mahal") else "ps"
        rec.update({f"gamma_{k_}_{t_}": x for t_, x in zip(TAUS, g)})
        rec[f"est_{k_}"] = d.mean()
        dd = d.astype(np.float32)                   # the Hodges-Lehmann estimate: the rank test's own
        hl = float(np.median((dd[:, None] + dd[None, :])[np.triu_indices(len(dd))] / 2))
        rec[f"hl_{k_}"] = hl
        print(f"  {lab:30s} " + " ".join(f"{x:15.2f}" for x in g) + f"   estimate ${d.mean():,.0f}, "
              f"Hodges-Lehmann ${hl:,.0f}")
        uo = np.exp(0.16 * np.abs(u[a1] - u[b1]))
        to = within_pair_odds(lt, a1, b1)
        print(f"  {'':30s} employability's within-pair odds ratio: median {np.median(uo):.2f}, "
              f"95th percentile {np.quantile(uo, 0.95):.2f}")
        print(f"  {'':30s} true score's within-pair odds ratio: median {np.median(to):.2f}, "
              f"95th percentile {np.quantile(to, 0.95):.1f}")
        mo = E["mutual_obligation_status"].values
        big = to > 10
        mo_diff = (mo[a1] == "Intensive") != (mo[b1] == "Intensive")
        rec.update({f"uo_med_{k_}": np.median(uo), f"uo_p95_{k_}": np.quantile(uo, 0.95),
                    f"to_med_{k_}": np.median(to), f"to_p95_{k_}": np.quantile(to, 0.95),
                    f"big_{k_}": 100 * big.mean(), f"big_mo_{k_}": 100 * mo_diff[big].mean()})
        print(f"  {'':30s} pairs with a true odds ratio above 10: {100 * big.mean():.1f}%, of which "
              f"{100 * np.mean(((mo[a1] == 'Intensive') != (mo[b1] == 'Intensive'))[big]):.0f}% "
              f"differ in intensive mutual obligation")

    banner("Table 10.4 - the cost per participant at which the earnings gain would pay, 2019 dollars")
    _, m0 = outcome_fits(Qdf, D, y)
    Zi, beta = logit_design(X, D)
    est = {"Odds weighting": (att_odds(D, y, att_weights(ps, D)), sandwich_se(Zi, beta, D, y, "ATT")),
           "Mahalanobis matching": ((y[ht] - y[hc]).mean(), paired_se(y[ht] - y[hc]))}
    print(f"  {'Years the gain lasts':22s} " + " ".join(f"{k:>22s} {'lower bound':>12s}" for k in est))
    for yrs in (1, 3, 5):
        f = sum(1 / (1 + DISCOUNT) ** t for t in range(yrs))
        for k, (e, s) in est.items():
            kk = "odds" if k.startswith("Odds") else "maha"
            rec[f"be_{kk}_{yrs}"], rec[f"be_{kk}_{yrs}_lo"] = e * f, (e - 1.96 * s) * f
        cells = " ".join(f"{e * f:22,.0f} {(e - 1.96 * s) * f:12,.0f}" for e, s in est.values())
        print(f"  {yrs:<22d} {cells}")
    for k, (e, s) in est.items():
        print(f"  {k}: ${e:,.0f} (se ${s:,.0f}); per 1,000 participants ${e * 1000 / 1e6:,.1f} million a year")
    print(f"  discount rate {100 * DISCOUNT:.0f} per cent; true ATT ${tau[D == 1].mean():,.0f}")
    for k, (e, s) in est.items():
        kk = "odds" if k.startswith("Odds") else "maha"
        rec[f"policy_est_{kk}"], rec[f"policy_se_{kk}"] = e, s
    rec["true_att"] = tau[D == 1].mean()
    a.outdir.mkdir(parents=True, exist_ok=True)
    pd.Series(rec, name="value").rename_axis("quantity").to_csv(a.outdir / "sensitivity_primary.csv")

    figure(r, out, a.outdir)


def figure(r, out, outdir):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.linewidth": 0.8,
                         "axes.labelsize": 8.5, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
                         "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.facecolor": "white"})
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    dz = np.linspace(0, 0.005, 201)
    yz = np.linspace(0, 0.05, 201)
    DZ, YZ = np.meshgrid(dz, yz)
    Z = r["est"] - adjusted(r["est"], r["se"], r["df"], DZ, YZ)        # the largest bias
    levels = [100, 250, 500, 1000]
    cs = ax.contour(DZ, YZ, Z, levels=levels, colors="0.45", linewidths=0.6,
                    linestyles=[":", "--", "-.", "-"])
    ax.clabel(cs, fmt=lambda v: f"${v:,.0f}", fontsize=7)
    pts = [("bench_edu_1", "as strong as education", "o", (-4, -12), "right"),
           ("bench_edu_3", "three times education", "o", (6, 2), "left"),
           ("bench_log_inc_2016_1", "as strong as log earnings 2016", "s", (6, 2), "left"),
           ("bench_fn_2016_1", "as strong as fortnights on payment", "^", (6, -3), "left")]
    for key, lab, mk, off, ha in pts:
        x_, y_, a_ = out[key]
        ax.scatter([x_], [y_], marker=mk, s=24, facecolors="white", edgecolors="black", zorder=3)
        ax.annotate(lab, (x_, y_), xytext=off, textcoords="offset points", fontsize=7, ha=ha)
    x_, y_, a_ = out["u"]
    ax.scatter([x_], [y_], marker="*", s=90, color="black", zorder=4)
    ax.annotate("employability (truth file)", (x_, y_), xytext=(7, -2),
                textcoords="offset points", fontsize=7, fontweight="bold")
    ax.set_xlabel("Share of residual variance in treatment explained by the confounder")
    ax.set_ylabel("Share of residual variance in earnings\nexplained by the confounder")
    ax.set_xlim(0, 0.005); ax.set_ylim(0, 0.05)
    for sp_ in ("top", "right"):
        ax.spines[sp_].set_visible(False)
    for ext in ("tif", "png"):
        fig.savefig(outdir / f"figure_10_1_sensitivity.{ext}")
    print(f"\n  wrote figure_10_1_sensitivity.tif to {outdir}")


if __name__ == "__main__":
    main()
