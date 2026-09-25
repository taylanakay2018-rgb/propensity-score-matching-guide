#!/usr/bin/env python3
"""
Script 3.5 — Six specifications, ranked by prediction and by bias
==================================================================
Chapter 3, Section 3.5. Produces Table 3.3 and Figure 3.1.

Six specifications through an identical downstream pipeline, each scored
against the known treatment effect, each repeated across five independent
draws. The ranking by predictive performance and the ranking by bias agree at
the bottom of the table and disagree at the top.

This script generates its own draws, because a single draw cannot separate the
differences it reports from sampling variability, so --datadir is ignored.

    python ch03/03_05_specifications.py
    python ch03/03_05_specifications.py --quick    # one draw, no figure
"""
import sys, subprocess, tempfile
import atexit, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _common3 import (cli, banner, load_analysis, design_matrix, eligible_only,
                      fit_propensity, stabilised_weights, match, matched_bias, REPO)
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score

DEMO = ["age", "female", "kids", "edu"]
LOC = ["remote", "seifa"]
HIST = ["fn_2016", "lts", "gp", "mh", "log_inc_2014", "log_inc_2015", "log_inc_2016",
        "inc_2014_missing", "inc_2015_missing", "inc_2016_missing",
        "drop_2016", "drop_missing"]
SEEDS = [20260808, 20260809, 20260810, 20260811, 20260812]


def one_draw(seed, tmp):
    out = tmp / f"d{seed}"
    subprocess.run([sys.executable, str(REPO / "make_data.py"), "--seed", str(seed),
                    "--n", "50000", "--outdir", str(out), "--quiet"], check=True)
    for s in ("ch02/02_05_link_modules.py", "ch02/02_06_reshape_panel.py"):
        subprocess.run([sys.executable, str(REPO / s), "--datadir", str(out)],
                       check=True, capture_output=True)
    E = eligible_only(load_analysis(out, with_truth=True))
    X = design_matrix(E)
    D = E["_treated"].values.astype(int)
    y = np.where(D == 1, E["_y1"], E["_y0"])
    tau = E["_tau_i"].values
    MO = pd.get_dummies(E["mutual_obligation_status"], prefix="mo",
                        drop_first=True).astype(float)
    MO.index = X.index
    Xi = X.copy()
    Xi["fn_sq"] = X.fn_2016 ** 2
    Xi["fn_x_lts"] = X.fn_2016 * X.lts
    Xi["inc_x_edu"] = X.log_inc_2016 * X.edu

    specs = [("1  Demographics only", X[DEMO], "logit"),
             ("2  + location", X[DEMO + LOC], "logit"),
             ("3  + payment and income history", X[DEMO + LOC + HIST], "logit"),
             ("4  + interactions", Xi, "logit"),
             ("5  + near-instrument", pd.concat([X, MO], axis=1), "logit"),
             ("6  Gradient boosting on set 3", X, "gbm")]
    rows = []
    for name, Xs, kind in specs:
        ps = fit_propensity(Xs, D, kind, seed)
        mt, mc, un = match(ps, D)
        bias, _, _ = matched_bias(mt, mc, y, tau)
        rows.append(dict(seed=seed, spec=name, auc=roc_auc_score(D, ps), bias=bias,
                         unmatched=un, maxw=stabilised_weights(ps, D).max()))
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
    # Saved beside the figure, as Scripts 4.3 and 5.3 do, so that audit.py can
    # hold Tables 3.3 and 3.4 to the draws rather than to a copy of them.
    a.outdir.mkdir(parents=True, exist_ok=True)
    t.to_csv(a.outdir / "specification_results.csv", index=False)
    g = t.groupby("spec").agg(auc=("auc", "mean"), bias=("bias", "mean"),
                              sd=("bias", "std"), unmatched=("unmatched", "mean"),
                              maxw=("maxw", "mean"))
    banner(f"Table 3.3 - six specifications, {len(seeds)} draw(s)")
    print(f"  {'Specification':32s} {'AUC':>6s} {'Bias':>8s} {'sd':>6s} "
          f"{'Unmat':>6s} {'MaxW':>6s}")
    for k, r in g.iterrows():
        sd = "-" if np.isnan(r.sd) else f"{r.sd:.1f}"
        print(f"  {k:32s} {r.auc:6.3f} {r.bias:+7.1f}% {sd:>6s} "
              f"{r.unmatched:6.0f} {r.maxw:6.1f}")
    print("\n  Rank by AUC   :", ", ".join(x[0] for x in
          g.sort_values("auc", ascending=False).index))
    print("  Rank by |bias|:", ", ".join(x[0] for x in
          g.reindex(g.bias.abs().sort_values().index).index))
    print("\n  The two rankings agree at the bottom and disagree at the top,")
    print("  which is the worst possible arrangement for anyone choosing on fit.")

    # Table 3.4 compares specification 3 (logistic) with specification 6
    # (boosting, same covariates) by consequence; these rows are five-draw.
    s3 = [k for k in g.index if k.startswith("3 ")][0]
    s6 = [k for k in g.index if k.startswith("6 ")][0]
    banner(f"Table 3.4 - five-draw rows, {len(seeds)} draw(s)")
    print(f"  {'':36s} {'Logistic':>12s} {'Boosting':>12s}")
    for label, col, fmt in [("Treated left unmatched", "unmatched", "{:.0f}"),
                            ("Largest stabilised weight", "maxw", "{:.1f}"),
                            ("Bias of the matched estimate (%)", "bias", "{:+.1f}"),
                            ("Standard deviation of that bias", "sd", "{:.1f}")]:
        print(f"  {label:36s} {fmt.format(g.loc[s3, col]):>12s} "
              f"{fmt.format(g.loc[s6, col]):>12s}")

    if a.quick:
        print("\n  --quick: skipping Figure 3.1, which needs all five draws.")
        return
    _figure(g, a.outdir)


def _figure(g, outdir):
    """Two panels. The first would mislead on its own, which is the point."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.linewidth": 0.8,
                         "axes.labelsize": 8.5, "xtick.labelsize": 7.5,
                         "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
                         "legend.frameon": False, "savefig.dpi": 300,
                         "savefig.bbox": "tight", "savefig.facecolor": "white"})
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(6.9, 3.0))

    # (a) all six, signed bias. Specifications 1 and 2 dominate the range and
    # create the appearance of a relationship between prediction and bias.
    for k, r in g.iterrows():
        n = k.strip()[0]
        axa.scatter(r.auc, r.bias, s=32, facecolors="white", edgecolors="black",
                    linewidths=0.9, zorder=3)
        axa.annotate(n, (r.auc, r.bias), textcoords="offset points",
                     xytext=(6, 2), fontsize=8)
    axa.axhline(0, color="black", linewidth=0.8)
    axa.set_xlabel("Area under the ROC curve")
    axa.set_ylabel("Bias of the matched estimate (%)")
    axa.set_title("all six specifications", fontsize=9)

    # (b) the four a researcher would actually choose between, with the spread.
    sub = g[[k.strip()[0] in "3456" for k in g.index]]
    for k, r in sub.iterrows():
        n = k.strip()[0]
        axb.errorbar(r.auc, r.bias, yerr=r.sd, fmt="o", markersize=5.5,
                     markerfacecolor="white", markeredgecolor="black",
                     ecolor="black", elinewidth=0.8, capsize=2.5, zorder=3)
        axb.annotate(n, (r.auc, r.bias), textcoords="offset points",
                     xytext=(7, 3), fontsize=8)
    axb.axhline(0, color="black", linewidth=0.8)
    axb.set_xlabel("Area under the ROC curve")
    axb.set_ylabel("Bias of the matched estimate (%)")
    axb.set_title("the four worth choosing between", fontsize=9)

    for ax, letter in ((axa, "a"), (axb, "b")):
        ax.text(-0.02, 1.08, f"({letter})", transform=ax.transAxes, fontsize=10,
                fontweight="bold", va="bottom", ha="right")
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    fig.subplots_adjust(wspace=0.35)
    outdir.mkdir(parents=True, exist_ok=True)
    for ext in ("tif", "png"):
        fig.savefig(outdir / f"figure_3_1_prediction_against_bias.{ext}")
    print(f"\n  wrote figure_3_1_prediction_against_bias.tif to {outdir}")


if __name__ == "__main__":
    main()
