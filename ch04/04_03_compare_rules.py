#!/usr/bin/env python3
"""
Script 4.3 — What each trimming rule costs
===========================================
Chapter 4, Sections 4.4 and 4.5. Produces Tables 4.3 and 4.4, and Figure 4.1.

Each rule is scored for the average treatment effect and for the effect on the
treated, on both scores of Chapter 3, against the truth for the sample the
rule retains. Scoring against the retained truth is the point: trimming moves
the estimand as well as the estimate.

This script generates its own draws and ignores --datadir.

    python ch04/04_03_compare_rules.py
    python ch04/04_03_compare_rules.py --quick
"""
import sys, subprocess, tempfile
import atexit, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _common4 import (cli, banner, score, trimming_rules, ate_ipw, att_odds, REPO)
import numpy as np, pandas as pd

SEEDS = [20260808, 20260809, 20260810, 20260811, 20260812]


def one_draw(seed, tmp):
    out = tmp / f"d{seed}"
    subprocess.run([sys.executable, str(REPO / "make_data.py"), "--seed", str(seed),
                    "--n", "50000", "--outdir", str(out), "--quiet"], check=True)
    for s in ("ch02/02_05_link_modules.py", "ch02/02_06_reshape_panel.py"):
        subprocess.run([sys.executable, str(REPO / s), "--datadir", str(out)],
                       check=True, capture_output=True)
    rows = []
    for est in ("logit", "gbm"):
        s = score(out, est, with_truth=True)
        ps, D, y, tau = s["ps"], s["D"], s["y"], s["tau"]
        for name, keep in trimming_rules(ps, D).items():
            Dk, yk, tk, pk = D[keep], y[keep], tau[keep], ps[keep]
            if Dk.sum() < 50 or (Dk == 0).sum() < 50:
                continue
            ate, se_ate = ate_ipw(pk, Dk, yk)
            att, se_att = att_odds(pk, Dk, yk)
            rows.append(dict(seed=seed, score=est, rule=name,
                             removed=int((~keep).sum()), retained=int(keep.sum()),
                             ate_true=tk.mean(), att_true=tk[Dk == 1].mean(),
                             ate_bias=100 * (ate - tk.mean()) / tk.mean(),
                             att_bias=100 * (att - tk[Dk == 1].mean()) / tk[Dk == 1].mean(),
                             se_ate=se_ate, se_att=se_att))
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
    # This script makes its own draws, so the results do not belong beside any
    # one dataset; they go with the figure.
    a.outdir.mkdir(parents=True, exist_ok=True)
    t.to_csv(a.outdir / "trimming_results.csv", index=False)

    g = t.pivot_table(index="rule", columns="score",
                      values=["ate_bias", "att_bias", "removed"], aggfunc="mean")
    banner(f"Table 4.3 - bias under each rule, by score and estimand "
           f"({len(seeds)} draw(s))")
    print(f"  {'Rule':40s} {'ATE lgt':>9s} {'ATT lgt':>9s} "
          f"{'ATE gbm':>9s} {'ATT gbm':>9s} {'Removed':>14s}")
    for r in g.index:
        print(f"  {r:40s} {g.loc[r,('ate_bias','logit')]:+8.1f}% "
              f"{g.loc[r,('att_bias','logit')]:+8.1f}% "
              f"{g.loc[r,('ate_bias','gbm')]:+8.1f}% "
              f"{g.loc[r,('att_bias','gbm')]:+8.1f}% "
              f"{g.loc[r,('removed','logit')]:6,.0f} /{g.loc[r,('removed','gbm')]:6,.0f}")

    # Table 4.4 in the book is one draw, the primary dataset, because the
    # point is the direction of the change within a sample. Until v4.8 this
    # printed five-draw means under the Table 4.4 banner, which did not match.
    banner("Table 4.4 - what trimming does to precision (logistic score, seed 20260808)")
    lg = t[(t.score == "logit") & (t.seed == SEEDS[0])].groupby("rule").agg(
        retained=("retained", "mean"), se_ate=("se_ate", "mean"), se_att=("se_att", "mean"))
    base = lg.loc["0  no trimming", "se_ate"]
    print(f"  {'Rule':40s} {'Retained':>10s} {'SE(ATE)':>9s} {'SE(ATT)':>9s} {'dSE':>7s}")
    for r in lg.index:
        print(f"  {r:40s} {lg.loc[r,'retained']:10,.0f} {lg.loc[r,'se_ate']:9,.0f} "
              f"{lg.loc[r,'se_att']:9,.0f} {100*(lg.loc[r,'se_ate']/base-1):+6.0f}%")

    banner("The estimand moves too (Section 4.4.3)")
    et = t[t.score == "logit"].groupby("rule").agg(
        ate_true=("ate_true", "mean"), att_true=("att_true", "mean"))
    b0 = et.loc["0  no trimming"]
    for r in et.index:
        print(f"  {r:40s} true ATE ${et.loc[r,'ate_true']:7,.0f} "
              f"({100*(et.loc[r,'ate_true']/b0.ate_true-1):+5.1f}%)   "
              f"true ATT ${et.loc[r,'att_true']:7,.0f}")

    if a.quick:
        print("\n  --quick: skipping Figure 4.1, which needs all five draws.")
        return
    _figure(t, a.outdir)


def _figure(t, outdir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.linewidth": 0.8,
                         "axes.labelsize": 8.5, "xtick.labelsize": 7.5,
                         "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
                         "legend.frameon": False, "savefig.dpi": 300,
                         "savefig.bbox": "tight", "savefig.facecolor": "white"})
    g = t.groupby(["score", "rule"]).agg(
        removed=("removed", "mean"), retained=("retained", "mean"),
        ate=("ate_bias", "mean"), att=("att_bias", "mean")).reset_index()
    g["share"] = 100 * g.removed / (g.removed + g.retained)
    fig, axes = plt.subplots(1, 2, figsize=(6.9, 3.0), sharex=True)
    for ax, col, name in zip(axes, ("ate", "att"),
                             ("average treatment effect", "effect on the treated")):
        for est, marker in (("logit", "o"), ("gbm", "s")):
            # Rule 7 is excluded by name, not by magnitude: it is off the scale
            # in both panels and including it would hide everything else.
            sub = (g[(g.score == est) & (~g.rule.str.startswith("7"))]
                   .sort_values("share"))
            ax.plot(sub.share, sub[col], marker=marker, markersize=5,
                    markerfacecolor="white", markeredgecolor="black",
                    color="black", linewidth=0.8,
                    linestyle="-" if est == "logit" else "--",
                    label="logistic" if est == "logit" else "boosting")
            for _, r in sub.iterrows():
                ax.annotate(r.rule.strip()[0], (r.share, r[col]),
                            textcoords="offset points", xytext=(5, 3), fontsize=7)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_xlabel("Share of the eligible population removed (%)")
        ax.set_ylabel(f"Bias, {name} (%)")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    for ax, letter in zip(axes, "ab"):
        ax.text(-0.02, 1.07, f"({letter})", transform=ax.transAxes, fontsize=10,
                fontweight="bold", va="bottom", ha="right")
    axes[0].legend(loc="lower right")
    fig.subplots_adjust(wspace=0.32)
    outdir.mkdir(parents=True, exist_ok=True)
    for ext in ("tif", "png"):
        fig.savefig(outdir / f"figure_4_1_trimming_tradeoff.{ext}")
    print(f"\n  wrote figure_4_1_trimming_tradeoff.tif to {outdir}")
    print("  Rule 7 is excluded from both panels by name: at +66% and +81% on the")
    print("  ATE it would compress everything else to a flat line.")


if __name__ == "__main__":
    main()
