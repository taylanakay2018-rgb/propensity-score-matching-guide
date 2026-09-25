#!/usr/bin/env python3
"""
Script 5.3 — Where the variation actually is
=============================================
Chapter 5, Sections 5.4 to 5.12. Produces Tables 5.2 to 5.7 and Figure 5.1,
the trimming check of Section 5.4, and Section 5.6's comparison of
Mahalanobis distance over four covariates with the same over all eighteen.

The central comparison of the chapter: how much the estimate moves when the
matching procedure changes, against how much it moves when only the draw
changes. It generates its own draws and ignores --datadir for that reason.

    python ch05/05_03_compare_variants.py
    python ch05/05_03_compare_variants.py --quick
"""
import sys, subprocess, tempfile
import atexit, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _common5 import (cli, banner, score, nn_match, mahalanobis_match,
                      optimal_match, linear_predictor, matched_att, trimming_rules,
                      REPO)
from _common4 import crump_alpha
import numpy as np, pandas as pd
from sklearn.linear_model import LinearRegression

SEEDS = [20260808, 20260809, 20260810, 20260811, 20260812, 20260813]
# Table 5.4 uses twelve draws rather than six. On six, the Mahalanobis
# improvement was smaller than its own standard deviation and could not be
# distinguished from nothing; see Section 5.6.
SEEDS_MAHA = SEEDS + [20260814, 20260815, 20260816, 20260817, 20260818, 20260819]


def one_draw(seed, tmp):
    out = tmp / f"d{seed}"
    subprocess.run([sys.executable, str(REPO / "make_data.py"), "--seed", str(seed),
                    "--n", "50000", "--outdir", str(out), "--quiet"], check=True)
    for s in ("ch02/02_05_link_modules.py", "ch02/02_06_reshape_panel.py"):
        subprocess.run([sys.executable, str(REPO / s), "--datadir", str(out)],
                       check=True, capture_output=True)
    s = score(out, "logit", with_truth=True)
    X, D, ps, y, tau = s["X"], s["D"], s["ps"], s["y"], s["tau"]
    nt = int(D.sum())
    rows = []
    variants = ([("NN 1:1, no caliper", lambda: nn_match(ps, D, 1e9, False, 1))] +
                [(f"NN 1:1, caliper {c}", lambda c=c: nn_match(ps, D, c, False, 1))
                 for c in (0.2, 0.1, 0.05, 0.02)] +
                [("NN 1:1 with replacement, caliper 0.1", lambda: nn_match(ps, D, 0.1, True, 1)),
                 ("NN 1:2, caliper 0.1", lambda: nn_match(ps, D, 0.1, False, 2)),
                 ("NN 1:3, caliper 0.1", lambda: nn_match(ps, D, 0.1, False, 3)),
                 ("Mahalanobis within caliper 0.1", lambda: mahalanobis_match(X, D, ps, 0.1))])
    for name, fn in variants:
        mt, mc = fn()
        bias, _, se = matched_att(mt, mc, y, tau)
        reuse = pd.Series(mc).value_counts().max() if len(mc) else 0
        # The shift in the true ATT caused by the treated left unmatched; see
        # Section 5.11. Recorded here so the six-draw figures can be checked.
        shift = 100 * (tau[mt].mean() / tau[D == 1].mean() - 1) if len(mt) else np.nan
        rows.append(dict(seed=seed, variant=name, bias=bias, se=se, pairs=len(mt),
                         unmatched=nt - len(set(mt.tolist())), max_reuse=int(reuse),
                         att_shift=shift, att_all=tau[D == 1].mean(),
                         att_matched=tau[mt].mean() if len(mt) else np.nan))

    # Section 5.6: the same Mahalanobis matching with all eighteen covariates in
    # the distance rather than the four of MAHA_COLS.
    mt, mc = mahalanobis_match(X, D, ps, 0.1, cols=list(X.columns))
    bias, _, se = matched_att(mt, mc, y, tau)
    rows.append(dict(seed=seed, variant="_maha18", bias=bias, se=se, pairs=len(mt),
                     unmatched=nt - len(set(mt.tolist())), max_reuse=1,
                     ncols=X.shape[1]))

    # Section 5.8: optimal against greedy, identical inputs.
    ot, oc, T, C = optimal_match(ps, D, 0.1, seed=seed)
    lp = linear_predictor(ps); cal = 0.1 * lp.std()
    M = np.abs(lp[T][:, None] - lp[C][None, :])
    taken = np.zeros(len(C), bool); pairs = []
    for k in np.argsort(-ps[T]):
        d = M[k].copy(); d[taken] = np.inf; j = int(np.argmin(d))
        if d[j] <= cal:
            pairs.append((T[k], C[j])); taken[j] = True
    P = np.array(pairs)
    ob, _, _ = matched_att(ot, oc, y, tau)
    gb, _, _ = matched_att(P[:, 0], P[:, 1], y, tau)
    rows.append(dict(seed=seed, variant="_optimal", bias=ob, se=np.nan,
                     pairs=len(ot), unmatched=0, max_reuse=1,
                     dist=np.abs(lp[ot] - lp[oc]).sum()))
    rows.append(dict(seed=seed, variant="_greedy_same", bias=gb, se=np.nan,
                     pairs=len(P), unmatched=0, max_reuse=1,
                     dist=np.abs(lp[P[:, 0]] - lp[P[:, 1]]).sum()))

    # Section 5.12: regression adjustment and bias correction.
    for lab, fn in [("_ra_ps", lambda: nn_match(ps, D, 0.1, False, 1)),
                    ("_ra_maha", lambda: mahalanobis_match(X, D, ps, 0.1))]:
        mt, mc = fn(); truth = tau[mt].mean()
        m0 = LinearRegression().fit(X.iloc[np.where(D == 0)[0]].values, y[D == 0])
        corr = (y[mt] - y[mc] - (m0.predict(X.iloc[mt].values)
                                 - m0.predict(X.iloc[mc].values))).mean()
        Xs = np.vstack([X.iloc[mt].values, X.iloc[mc].values])
        ys = np.r_[y[mt], y[mc]]
        ds = np.r_[np.ones(len(mt)), np.zeros(len(mc))]
        reg = LinearRegression().fit(np.c_[ds, Xs], ys).coef_[0]
        rows.append(dict(seed=seed, variant=lab,
                         bias=100 * ((y[mt] - y[mc]).mean() - truth) / truth,
                         biascorr=100 * (corr - truth) / truth,
                         regadj=100 * (reg - truth) / truth,
                         se=np.nan, pairs=len(mt), unmatched=0, max_reuse=1))

    # Section 5.4: the chapter matches on the untrimmed eligible population.
    # This is the check that doing so changes nothing the chapter concludes:
    # the same two variants on the population Chapter 4's rule retains.
    keep = trimming_rules(ps, D)["5  variance-minimising"]
    k = np.where(keep)[0]
    gone_t = np.where(~keep & (D == 1))[0]
    mt_all, _ = nn_match(ps, D, 0.1, False, 1)
    for lab, fn in [("_trim_ps", lambda p, d, x: nn_match(p, d, 0.1, False, 1)),
                    ("_trim_maha", lambda p, d, x: mahalanobis_match(x, d, p, 0.1))]:
        mt, mc = fn(ps[keep], D[keep], X.iloc[k].reset_index(drop=True))
        rows.append(dict(seed=seed, variant=lab,
                         bias=matched_att(k[mt], k[mc], y, tau)[0], se=np.nan,
                         pairs=len(mt), unmatched=int(D[keep].sum()) - len(set(mt.tolist())),
                         max_reuse=1, alpha=crump_alpha(ps), max_ps=float(ps.max()),
                         treated_removed=len(gone_t),
                         controls_removed=int((~keep & (D == 0)).sum()),
                         removed_were_matched=int(np.isin(gone_t, mt_all).sum()),
                         max_ps_removed_treated=float(ps[gone_t].max()) if len(gone_t) else np.nan,
                         att_all=tau[D == 1].mean(), att_kept=tau[keep & (D == 1)].mean()))
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
    # The Mahalanobis comparison needs more draws than the rest; see Section 5.6.
    maha_rows = []
    if not a.quick:
        for s2 in SEEDS_MAHA[len(seeds):]:
            extra = [r for r in one_draw(s2, tmp)
                     if r["variant"] in ("Mahalanobis within caliper 0.1",
                                         "NN 1:1, caliper 0.1", "_maha18")]
            maha_rows += extra
            print(f"  extra draw {s2} done", file=sys.stderr, flush=True)
    t = pd.DataFrame(rows)
    maha = pd.concat([t[t.variant.isin(["Mahalanobis within caliper 0.1",
                                        "NN 1:1, caliper 0.1", "_maha18"])],
                      pd.DataFrame(maha_rows)], ignore_index=True)
    a.outdir.mkdir(parents=True, exist_ok=True)
    t.to_csv(a.outdir / "matching_results.csv", index=False)
    # Table 5.4 draws on twelve draws, six of which are not in the file above.
    maha.to_csv(a.outdir / "matching_mahalanobis.csv", index=False)
    main_v = t[~t.variant.str.startswith("_")]

    g = main_v.groupby("variant").agg(bias=("bias", "mean"), sd=("bias", "std"),
                                      se=("se", "mean"), pairs=("pairs", "mean"),
                                      unmatched=("unmatched", "mean"),
                                      reuse=("max_reuse", "mean"))
    banner(f"Table 5.2 - nine matching variants, {len(seeds)} draw(s)")
    print(f"  {'Variant':38s} {'Bias':>8s} {'sd':>6s} {'SE':>6s} "
          f"{'Pairs':>8s} {'Unmat':>6s} {'Reuse':>6s}")
    for k, r in g.iterrows():
        sd = "-" if np.isnan(r.sd) else f"{r.sd:.1f}"
        print(f"  {k:38s} {r.bias:+7.1f}% {sd:>6s} {r.se:6,.0f} "
              f"{r.pairs:8,.0f} {r.unmatched:6,.0f} {r.reuse:6.1f}")

    cal = main_v[main_v.variant.str.startswith("NN 1:1, caliper")]
    w = cal.pivot(index="seed", columns="variant", values="bias")
    banner(f"Table 5.3 - the same four calipers, in each draw")
    print(w.round(2).to_string())
    spread = (w.max(axis=1) - w.min(axis=1))
    sd10 = w[[c for c in w.columns if "0.1" in c][0]].std()
    print(f"\n  within-draw spread across calipers: mean {spread.mean():.3f} pp, "
          f"max {spread.max():.3f} pp")
    if len(seeds) > 1:
        print(f"  between-draw standard deviation:    {sd10:.2f} pp")
        print(f"  the draw matters {sd10 / spread.mean():.0f} times more than the caliper")

    banner(f"Table 5.4 - Mahalanobis against propensity score, paired, "
           f"{maha.seed.nunique()} draw(s)")
    m = maha.pivot(index="seed", columns="variant", values="bias")
    m18 = m.pop("_maha18")
    m.columns = ["Mahalanobis", "PS nearest neighbour"]
    m["reduction"] = m["PS nearest neighbour"].abs() - m["Mahalanobis"].abs()
    print(m.round(2).to_string())
    mu, sd = m.reduction.mean(), m.reduction.std()
    se = sd / np.sqrt(len(m))
    print(f"\n  mean |bias|  PS {m['PS nearest neighbour'].abs().mean():.2f}%"
          f"   Mahalanobis {m.Mahalanobis.abs().mean():.2f}%")
    print(f"  mean reduction {mu:+.2f} pp (sd {sd:.2f}, se {se:.2f}, t {mu/se:.2f}), "
          f"better in {(m.reduction > 0).sum()} of {len(m)}")
    if len(m) <= 6:
        print("  Six draws cannot settle this; the chapter uses twelve. Run without")
        print("  --quick for the full comparison.")

    banner(f"Section 5.6 - Mahalanobis over all eighteen covariates against the four, "
           f"{len(m18)} draw(s)")
    c = pd.DataFrame({"four": m.Mahalanobis, "eighteen": m18})
    c["reduction"] = c.four.abs() - c.eighteen.abs()
    print(c.round(2).to_string())
    mu, sd = c.reduction.mean(), c.reduction.std()
    se = sd / np.sqrt(len(c))
    print(f"\n  mean |bias|  four {c.four.abs().mean():.2f}%   eighteen {c.eighteen.abs().mean():.2f}%")
    print(f"  sd of bias   four {c.four.std():.2f}    eighteen {c.eighteen.std():.2f}")
    print(f"  mean reduction from using eighteen {mu:+.2f} pp (sd {sd:.2f}, se {se:.2f}), "
          f"better in {(c.reduction > 0).sum()} of {len(c)}")

    banner("Table 5.5 - precision under 1:1, 1:2 and 1:3")
    r = g.loc[[v for v in g.index if v.startswith(("NN 1:1, caliper 0.1", "NN 1:2", "NN 1:3"))]]
    print(r[["bias", "sd", "se", "pairs", "unmatched"]].round(2).to_string())

    o = t[t.variant.isin(["_optimal", "_greedy_same"])].pivot(
        index="seed", columns="variant", values=["bias", "dist"])
    banner("Table 5.6 - optimal against greedy, identical inputs")
    print(f"  {'Draw':10s} {'Optimal':>9s} {'Greedy':>9s} {'Diff':>7s} {'Distance':>10s}")
    for s in o.index:
        ob, gb = o.loc[s, ("bias", "_optimal")], o.loc[s, ("bias", "_greedy_same")]
        od, gd = o.loc[s, ("dist", "_optimal")], o.loc[s, ("dist", "_greedy_same")]
        print(f"  {s:<10} {ob:+8.2f}% {gb:+8.2f}% {abs(gb)-abs(ob):+6.2f} "
              f"{100*(od/gd-1):+9.0f}%")

    banner("Table 5.7 - regression adjustment on the matched samples")
    ra = t[t.variant.isin(["_ra_ps", "_ra_maha"])].groupby("variant").agg(
        plain=("bias", "mean"), biascorr=("biascorr", "mean"), regadj=("regadj", "mean"))
    ra.index = ["Mahalanobis within a caliper", "Propensity score nearest neighbour"]
    print(ra.round(2).to_string())
    print("\n  Neither adjustment improved on the plain difference in these data.")

    banner("Section 5.4 - the same two variants on Chapter 4's trimmed population")
    tr = t[t.variant.isin(["_trim_ps", "_trim_maha"])]
    one = tr[tr.variant == "_trim_ps"]
    for lab, base, trim in [("Propensity score nearest neighbour", "NN 1:1, caliper 0.1", "_trim_ps"),
                            ("Mahalanobis within a caliper", "Mahalanobis within caliper 0.1", "_trim_maha")]:
        print(f"  {lab:36s} untrimmed {g.loc[base, 'bias']:+6.2f}%   "
              f"trimmed {tr[tr.variant == trim].bias.mean():+6.2f}%")
    print(f"\n  treated removed by the rule     {one.treated_removed.mean():7.1f} "
          f"(highest score removed {one.max_ps_removed_treated.max():.4f})")
    print(f"  ... of whom matched untrimmed   {one.removed_were_matched.mean():7.1f}")
    print(f"  controls removed by the rule    {one.controls_removed.mean():7.1f}")
    print(f"  threshold alpha                 {one.alpha.min():.3f} to {one.alpha.max():.3f}"
          f"  (upper threshold {1 - one.alpha.max():.3f}; highest score {one.max_ps.max():.3f})")
    print(f"  shift in the true ATT           "
          f"{(100 * (one.att_kept / one.att_all - 1)).mean():+.2f}%")

    if a.quick:
        print("\n  --quick: skipping Figure 5.1, which needs all six draws.")
        return
    _figure(main_v, cal, a.outdir)


def _figure(t, cal, outdir):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.linewidth": 0.8,
                         "axes.labelsize": 8.5, "xtick.labelsize": 7.5,
                         "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
                         "legend.frameon": False, "savefig.dpi": 300,
                         "savefig.bbox": "tight", "savefig.facecolor": "white"})
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(6.9, 3.2), sharey=True)
    seeds = sorted(t.seed.unique())
    for k, s in enumerate(seeds):
        v = t[t.seed == s].bias.values
        axa.scatter(np.full(len(v), k), v, s=16, facecolors="white",
                    edgecolors="black", linewidths=0.8, zorder=3)
    axa.axhline(0, color="black", linewidth=0.8)
    axa.set_xticks(range(len(seeds)))
    axa.set_xticklabels([str(s)[-2:] for s in seeds])
    axa.set_xlabel("Draw")
    axa.set_ylabel("Bias of the matched ATT (%)")
    axa.set_title("all nine variants, by draw", fontsize=9)
    w = cal.pivot(index="seed", columns="variant", values="bias")
    for c, mk in zip(w.columns, "os^D"):
        axb.plot(range(len(w)), w[c].values, marker=mk, markersize=4.5,
                 markerfacecolor="white", markeredgecolor="black", color="black",
                 linewidth=0.8, label=c.split("caliper ")[-1])
    axb.axhline(0, color="black", linewidth=0.8)
    axb.set_xticks(range(len(w)))
    axb.set_xticklabels([str(s)[-2:] for s in w.index])
    axb.set_xlabel("Draw")
    axb.set_title("the four calipers alone", fontsize=9)
    axb.legend(title="caliper", loc="upper left", ncol=2,
           bbox_to_anchor=(0.0, 0.99), handlelength=1.6, columnspacing=1.0)
    for ax, letter in ((axa, "a"), (axb, "b")):
        ax.text(-0.02, 1.07, f"({letter})", transform=ax.transAxes, fontsize=10,
                fontweight="bold", va="bottom", ha="right")
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    fig.subplots_adjust(wspace=0.12)
    outdir.mkdir(parents=True, exist_ok=True)
    for ext in ("tif", "png"):
        fig.savefig(outdir / f"figure_5_1_variation.{ext}")
    print(f"\n  wrote figure_5_1_variation.tif to {outdir}")
    print("  In panel (b) the four caliper lines lie on top of one another.")


if __name__ == "__main__":
    main()
