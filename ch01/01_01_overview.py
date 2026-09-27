#!/usr/bin/env python3
"""
Script 1.1 — The book in one figure: the problem, the true values and the designs
=================================================================================
Chapter 1, Sections 1.2, 1.5 and 1.6. Produces Figure 1.1 and the figures
quoted in those sections.

Panel (a) draws the causal structure that the generator of PLIDA-SIM builds in:
the observed confounders, the near-instrument, the pre-programme earnings
shock, the latent employability that no dataset records, and the pure outcome
predictor. Panel (b) sets the estimates of the book's principal designs on the
primary dataset beside the naive comparison and the truth. Every estimate is
computed here with the functions of the chapter that develops it, so the
figure previews Chapters 3 to 10 rather than summarising saved results.

The truth file is read for the true values and for scoring, as in every
chapter; nothing else here uses it.

    python ch01/01_01_overview.py
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
for d in ("ch09", "ch07", "ch06", "ch05", "ch03"):
    sys.path.insert(0, str(HERE.parent / d))
from _common9 import cli, banner, score, outcome_design, estimates          # noqa: E402
from _common6 import TRIM_RULE, trimming_rules, att_weights, att_odds, outcome_fits, att_regression  # noqa: E402
import numpy as np                                                            # noqa: E402
import pandas as pd                                                           # noqa: E402

ROWS = [("naive", "Naive difference in means", "1.2"),
        ("regression", "Outcome regression", "6.9"),
        ("odds", "Odds weighting", "6"),
        ("dr_att", "Doubly robust", "6"),
        ("sub20_reg", "20 strata, regression within strata", "7"),
        ("match", "PS matching, 1:1", "5"),
        ("maha", "Mahalanobis matching, 1:1", "5"),
        ("maha13", "Mahalanobis matching, 1:3", "5"),
        ("odds_gbm_trim", "Odds weighting, trimmed boosted score", "6")]


def true_values(datadir):
    """The three sets of true values of Section 1.5."""
    T = pd.read_csv(Path(datadir) / "truth" / "truth_parameters.csv").set_index("person_id")
    A = pd.read_csv(Path(datadir) / "analysis_file.csv").set_index("person_id")
    T = T.join(A[["eligible"]])
    t, e = T.treated == 1, T.eligible == 1
    # 2019 earnings as every chapter scores them: each person's realised potential outcome
    y = pd.Series(np.where(t, T.y1, T.y0), index=T.index)
    return {"n_all": len(T), "n_treated_all": int(t.sum()),
            "att_all": T.tau_i[t].mean(), "ate_all": T.tau_i.mean(),
            "naive_all": y[t].mean() - y[~t].mean(),
            "n_elig": int(e.sum()), "n_t_elig": int((t & e).sum()), "n_c_elig": int((~t & e).sum()),
            "att_elig": T.tau_i[t & e].mean(), "ate_elig": T.tau_i[e].mean(),
            "naive_elig": y[t & e].mean() - y[~t & e].mean()}


def main():
    a = cli(__doc__)
    v = true_values(a.datadir)
    banner("Sections 1.2 and 1.5 - the true values and the naive comparison, primary dataset")
    print(f"  all {v['n_all']:,} persons: {v['n_treated_all']:,} took part; true ATT ${v['att_all']:,.0f}, "
          f"true ATE ${v['ate_all']:,.0f}, naive difference ${v['naive_all']:,.0f}")
    print(f"  eligible population: {v['n_elig']:,} persons, {v['n_t_elig']:,} took part "
          f"({100 * v['n_t_elig'] / v['n_elig']:.1f} per cent); true ATT ${v['att_elig']:,.0f}, "
          f"true ATE ${v['ate_elig']:,.0f}, naive difference ${v['naive_elig']:,.0f}")

    sc = score(a.datadir, "logit", with_truth=True)
    E, X, D, ps, y, tau = sc["E"], sc["X"], sc["D"], sc["ps"], sc["y"], sc["tau"]
    Q = outcome_design(E, X, with_occupation=True)
    e, _ = estimates(X, D, y, Q, ps, full=True)
    _, m0 = outcome_fits(Q, D, y)
    e["naive"] = y[D == 1].mean() - y[D == 0].mean()
    e["regression"] = att_regression(D, y, m0)
    g = score(a.datadir, "gbm", with_truth=True)
    k = trimming_rules(g["ps"], g["D"])[TRIM_RULE]
    e["odds_gbm_trim"] = att_odds(g["D"][k], g["y"][k], att_weights(g["ps"][k], g["D"][k]))
    truth = {key: tau[D == 1].mean() for key, *_ in ROWS}
    truth["odds_gbm_trim"] = g["tau"][k & (g["D"] == 1)].mean()

    banner("Section 1.6 and Figure 1.1(b) - the designs of Chapters 3 to 10 on the primary dataset")
    print(f"  {'':40s} {'Estimate':>9s} {'Truth':>8s} {'Bias':>7s}  Chapter")
    rec = dict(v)
    for key, lab, ch in ROWS:
        b = 100 * (e[key] - truth[key]) / truth[key]
        print(f"  {lab:40s} {e[key]:9,.0f} {truth[key]:8,.0f} {b:+6.1f}%  {ch}")
        rec[f"est_{key}"], rec[f"truth_{key}"] = e[key], truth[key]
    a.outdir.mkdir(parents=True, exist_ok=True)
    pd.Series(rec, name="value").rename_axis("quantity").to_csv(a.outdir / "overview_primary.csv")
    figure(e, truth, v, a.outdir)


def figure(e, truth, v, outdir):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.ticker
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.linewidth": 0.8,
                         "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.facecolor": "white"})
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(10.4, 4.4), gridspec_kw={"width_ratios": [1.05, 1]})

    # (a) the causal structure the generator builds in
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    nodes = {"S": (0.13, 0.88, "Earnings shock\n(truth file)", True),
             "X": (0.58, 0.88, "Observed confounders:\nearnings, payments, education,\nhealth, location, age", False),
             "M": (0.10, 0.27, "Mutual obligation\nstatus", False),
             "U": (0.585, 0.43, "Latent\nemployability\n(truth file)", True),
             "O": (0.95, 0.52, "Occupation", False),
             "D": (0.36, 0.08, "Took part in\nthe programme", False),
             "Y": (0.86, 0.10, "Earnings\nin 2019", False)}
    art = {}
    for key, (x, y_, text, hidden) in nodes.items():
        art[key] = ax.text(x, y_, text, ha="center", va="center", fontsize=7.2, zorder=3,
                           bbox=dict(boxstyle="round,pad=0.45", fc="white", ec="black", lw=0.8,
                                     ls="--" if hidden else "-"))

    def arrow(a_, b_, dashed=False, rad=0.0):
        ax.annotate("", xy=(0.5, 0.5), xycoords=art[b_], xytext=(0.5, 0.5), textcoords=art[a_],
                    arrowprops=dict(arrowstyle="-|>", lw=0.8, color="black", shrinkA=2, shrinkB=2,
                                    linestyle="--" if dashed else "-", patchA=art[a_].get_bbox_patch(),
                                    patchB=art[b_].get_bbox_patch(),
                                    connectionstyle=f"arc3,rad={rad}"), zorder=2)
    for a_, b_, dsh, rad in (("S", "X", True, 0), ("S", "D", True, 0), ("X", "D", False, 0),
                             ("X", "Y", False, 0), ("M", "D", False, 0), ("U", "D", True, 0),
                             ("U", "Y", True, 0), ("O", "Y", False, 0), ("D", "Y", False, 0)):
        arrow(a_, b_, dsh, rad)
    ax.text(0.0, -0.05, "Dashed: not in the analysis file", fontsize=7, style="italic")
    ax.set_title("(a) What drives participation and earnings", fontsize=9, loc="left")

    # (b) the designs on the primary dataset against the truth
    ys = np.arange(len(ROWS))[::-1]
    for yy, (key, lab, ch) in zip(ys, ROWS):
        bx.plot([e[key]], [yy], "o", ms=5, mfc="black" if key != "naive" else "white", mec="black")
        bx.plot([truth[key]], [yy], "|", ms=9, color="black")
    bx.axvline(0, color="0.6", lw=0.6)
    bx.axvline(v["att_elig"], color="black", lw=0.6, ls=":")
    bx.text(v["att_elig"] + 80, len(ROWS) - 0.4, f"true ATT ${v['att_elig']:,.0f}", fontsize=7)
    bx.set_yticks(ys, [lab for _, lab, _ in ROWS], fontsize=7.5)
    bx.set_xlim(-5500, 8500)
    bx.set_ylim(-0.7, len(ROWS) - 0.1)
    bx.set_xlabel("Effect on 2019 earnings, dollars", fontsize=7.5)
    bx.tick_params(axis="x", labelsize=7.5)
    bx.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x_, _: f"{x_:,.0f}".replace("-", "\u2212")))
    for s_ in ("top", "right"):
        bx.spines[s_].set_visible(False)
    bx.set_title("(b) The primary dataset: estimates against the truth", fontsize=9, loc="left")
    fig.tight_layout(w_pad=2.0)
    for ext in ("tif", "png"):
        fig.savefig(outdir / f"figure_1_1_overview.{ext}")
    print(f"\n  wrote figure_1_1_overview.tif to {outdir}")


if __name__ == "__main__":
    main()
