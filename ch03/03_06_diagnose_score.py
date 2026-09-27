#!/usr/bin/env python3
"""
Script 3.6 — Diagnosing the fitted score
=========================================
Chapter 3, Section 3.8. Produces Table 3.6 and Figure 3.2.

Four diagnostics, none of which uses the outcome: range, weight tail, overlap,
and the counts of persons with no counterpart in the other condition. These
are what Chapter 4 acts on.

    python ch03/03_06_diagnose_score.py
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common3 import (cli, banner, load_analysis, design_matrix, eligible_only,
                      fit_propensity, stabilised_weights, effective_n)
import numpy as np, pandas as pd


def diagnose(ps, D):
    w = stabilised_weights(ps, D)
    tr, ct = ps[D == 1], ps[D == 0]
    dec = pd.crosstab(pd.qcut(ps, 10, labels=False, duplicates="drop"), D)
    return {
        "range": f"{ps.min():.3f} to {ps.max():.3f}",
        "mean vs rate": f"{ps.mean():.4f} / {D.mean():.4f}",
        "largest stabilised weight": f"{w.max():.1f}",
        "effective control sample": f"{effective_n(w[D == 0]):,.0f}",
        "treated above highest control": f"{int((tr > ct.max()).sum()):,}",
        "controls below lowest treated": f"{int((ct < tr.min()).sum()):,}",
        "persons with a score above 0.5": f"{int((ps > 0.5).sum()):,}",
        # Table 3.6 prints this row; until v4.9 the script did not compute it.
        "persons with a score above 0.7": f"{int((ps > 0.7).sum()):,}",
        # The decile with the fewest treated, and that same decile's size (as
        # Script 4.1 now does; the smallest decile is a different one).
        "smallest decile treated cell": f"{int(dec[1].min()):,} of "
                                        f"{int(dec.loc[dec[1].idxmin()].sum()):,}",
    }, dec


def main():
    a = cli(__doc__)
    E = eligible_only(load_analysis(a.datadir))
    X, D = design_matrix(E), E["treated"].values
    scores = {"logistic": fit_propensity(X, D, "logit"),
              "boosting": fit_propensity(X, D, "gbm", seed=20260808)}
    res = {k: diagnose(v, D)[0] for k, v in scores.items()}

    banner("Table 3.6 - diagnostics for the fitted score, before any trimming")
    print(f"  {'Diagnostic':34s} {'Logistic':>16s} {'Boosting':>16s}")
    for k in res["logistic"]:
        print(f"  {k:34s} {res['logistic'][k]:>16s} {res['boosting'][k]:>16s}")
    print("\n  Mean score and observed rate agree by construction under maximum")
    print("  likelihood. That agreement is not evidence the model is any good.")
    print("\n  In the DataLab, report the 1st and 99th percentiles rather than the")
    print("  range: an extreme propensity score can identify the person holding it.")
    for k, ps in scores.items():
        lo, hi = np.percentile(ps, [1, 99])
        print(f"    {k:9s} 1st-99th percentile {lo:.3f} to {hi:.3f}")

    _figure(scores, D, a.outdir)


def _figure(scores, D, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.linewidth": 0.8,
                         "axes.labelsize": 8.5, "xtick.labelsize": 7.5,
                         "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
                         "legend.frameon": False, "savefig.dpi": 300,
                         "savefig.bbox": "tight", "savefig.facecolor": "white"})
    fig, axes = plt.subplots(1, 2, figsize=(6.9, 2.9), sharex=True, sharey=True)
    bins = np.linspace(0, 1, 51)
    for ax, (name, ps), letter in zip(axes, scores.items(), "ab"):
        # Counts on a log scale, not densities. The point of the figure is the
        # handful of treated persons past the highest control score, and on a
        # linear scale a group of five is invisible beside a mode of 4,000.
        ax.hist(ps[D == 0], bins=bins, histtype="step", color="black",
                linewidth=0.9, label="control")
        ax.hist(ps[D == 1], bins=bins, histtype="stepfilled", facecolor="none",
                edgecolor="black", hatch="////", linewidth=0.7, label="treated")
        cmax = ps[D == 0].max()
        ax.axvline(cmax, color="black", linewidth=0.8, linestyle=(0, (4, 3)))
        beyond = int((ps[D == 1] > cmax).sum())
        ax.annotate(f"{beyond} treated\nwith no match", xy=(cmax, 1.6),
                    xytext=(0.60, 0.74), textcoords="axes fraction", fontsize=7,
                    ha="left", va="center",
                    arrowprops=dict(arrowstyle="->", linewidth=0.7, color="black",
                                    connectionstyle="arc3,rad=0.2"))
        ax.set_yscale("log")
        ax.set_ylim(0.7, 2e4)
        ax.set_xlim(0, 1)
        ax.set_xlabel("Fitted propensity score")
        ax.set_title(name, fontsize=9)
        ax.text(-0.02, 1.06, f"({letter})", transform=ax.transAxes, fontsize=10,
                fontweight="bold", va="bottom", ha="right")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].set_ylabel("Persons (log scale)")
    axes[0].legend(loc="upper right")
    fig.subplots_adjust(wspace=0.15)
    outdir.mkdir(parents=True, exist_ok=True)
    for ext in ("tif", "png"):
        fig.savefig(outdir / f"figure_3_2_overlap.{ext}")
    print(f"\n  wrote figure_3_2_overlap.tif to {outdir}")
    print("  The dashed line is the highest control score. Treated mass to its")
    print("  right has no possible match, and Chapter 4 decides what to do with it.")


if __name__ == "__main__":
    main()
