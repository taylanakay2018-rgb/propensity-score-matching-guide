#!/usr/bin/env python3
"""
Script 9.2 — Which standard errors are right, across many draws
===============================================================
Chapter 9, Sections 9.4 to 9.8. Produces Tables 9.2 to 9.5 and Figure 9.1.

Every estimator of Chapters 5 to 7 on the logistic score, untrimmed, with every
candidate standard error, repeated across independent draws. A standard error
is right if it matches the standard deviation of the estimation error across
draws, and a 95 per cent interval is right if it contains the truth in 95 per
cent of draws.

The book's tables come from the full run: 200 draws, with the bootstrap (100
replicates, the score refitted each time) on the first 40. That takes about
three hours on two cores, so its results are committed to the repository as
results/ch09_standard_errors_200.csv, and this script reads them. By default it
also runs the first 40 draws again, with the bootstrap on the first 5, and
confirms that they reproduce the committed rows exactly. The truth file is
read to score the estimates.

It generates its own draws and ignores --datadir.

    python ch09/09_02_standard_errors_across_draws.py                 # 40 draws, then report
    python ch09/09_02_standard_errors_across_draws.py --draws 200 --boot-draws 40 --commit
    python ch09/09_02_standard_errors_across_draws.py --quick         # 1 draw
"""
import sys, tempfile, argparse
import atexit, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _common9 import (banner, score, make_draw, outcome_design, all_standard_errors,
                      COMMITTED, FIRST_SEED, B_FULL, LABELS, REPO)
import numpy as np, pandas as pd

ORDER = ["odds", "dr_att", "sub20", "sub20_reg", "match", "match_repl", "maha", "maha13",
         "ipw_ate", "dr_ate"]
# The standard error Section 9.9 recommends for each estimator.
RECOMMENDED = {"odds": "se_sandwich", "ipw_ate": "se_sandwich", "dr_att": "se_boot",
               "dr_ate": "se_boot", "sub20": "se_boot", "sub20_reg": "se_boot",
               "match": "se_paired", "match_repl": "se_ai", "maha": "se_paired",
               "maha13": "se_paired"}
METHODS = [("se_naive", "score known"), ("se_sandwich", "sandwich"), ("se_boot", "bootstrap"),
           ("se_paired", "paired"), ("se_unpaired", "unpaired"), ("se_ai", "Abadie-Imbens"),
           ("se_boot_sets", "matched-set bootstrap"), ("se_wls_robust", "WLS robust")]
KEY = ["seed", "estimator", "est", "truth"]


def run(first, n, boot_draws, tmp):
    parts = []
    for s in range(first, first + n):
        out = make_draw(s, tmp)
        sc = score(out, "logit", with_truth=True)
        E, X, D, ps, y, tau = sc["E"], sc["X"], sc["D"], sc["ps"], sc["y"], sc["tau"]
        Q = outcome_design(E, X, with_occupation=True)
        B = B_FULL if s < first + boot_draws else 0
        r, _ = all_standard_errors(X, D, y, Q, ps, tau, s, B=B)
        parts.append(r)
        shutil.rmtree(out, ignore_errors=True)
        print(f"  draw {s} done", file=sys.stderr, flush=True)
    return pd.concat(parts, ignore_index=True)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--draws", type=int, default=40)
    p.add_argument("--boot-draws", type=int, default=5)
    p.add_argument("--quick", action="store_true")
    p.add_argument("--first", type=int, default=FIRST_SEED,
                   help="first seed; the full run can be split across processes")
    p.add_argument("--part", type=Path, default=None,
                   help="write this run's rows here and stop (for a split full run)")
    p.add_argument("--commit", action="store_true",
                   help="write this run's results to the committed file (full run only)")
    p.add_argument("--outdir", type=Path, default=REPO / "figures")
    p.add_argument("--datadir", type=Path, default=None)       # accepted, ignored
    a = p.parse_args()
    n, nb = (1, 0) if a.quick else (a.draws, a.boot_draws)
    tmp = Path(tempfile.mkdtemp())
    atexit.register(shutil.rmtree, tmp, ignore_errors=True)   # leave no draws behind
    t = run(a.first, n, nb, tmp)
    if a.part:
        t.to_csv(a.part, index=False)
        return
    a.outdir.mkdir(parents=True, exist_ok=True)
    t.to_csv(a.outdir / "se_results.csv", index=False)
    if a.commit:
        COMMITTED.parent.mkdir(exist_ok=True)
        t.to_csv(COMMITTED, index=False)

    banner(f"This run: {t.seed.nunique()} draw(s), bootstrap on {nb}")
    if COMMITTED.exists() and not a.commit:
        c = pd.read_csv(COMMITTED)
        m = t.merge(c, on=["seed", "estimator"], suffixes=("", "_c"))
        cols = [x for x in t.columns if x not in ("seed", "estimator") and x + "_c" in m.columns]
        gap = max(float(np.nanmax(np.abs(m[x] - m[x + "_c"]))) if m[x].notna().any() else 0.0
                  for x in cols)
        print(f"  reproduces the committed rows for the same draws: largest difference {gap:.1e}"
              f" over {len(m)} rows")
        full = c
    else:
        full = t
    report(full, a.outdir)


def spread(t):
    t = t.assign(err=t.est - t.truth)
    return t.groupby("estimator").err.std()


def report(t, outdir):
    nd, nbd = t.seed.nunique(), t.dropna(subset=["se_boot"]).seed.nunique()
    t = t.assign(err=t.est - t.truth, bias=100 * (t.est - t.truth) / t.truth)
    sp = t.groupby("estimator").err.std()
    bsub = t.dropna(subset=["se_boot"])
    sp_b = bsub.groupby("estimator").err.std()

    banner(f"Table 9.2 - standard error over actual spread, {nd} draws (bootstrap: {nbd})")
    print(f"  {'':34s} {'Spread':>8s} " + " ".join(f"{lab[:10]:>10s}" for _, lab in METHODS))
    for k in ORDER:
        q = t[t.estimator == k]
        cells = []
        for m, _ in METHODS:
            if m not in q or q[m].isna().all():
                cells.append(f"{'':>10s}")
            else:
                ref = sp_b[k] if m == "se_boot" else sp[k]
                cells.append(f"{q[m].mean() / ref:10.2f}")
        print(f"  {LABELS[k]:34s} {sp[k]:8,.0f} " + " ".join(cells))
    print(f"  bootstrap ratios are against the spread over the {nbd} bootstrapped draws")
    r = t[t.estimator == "match_repl"]
    print(f"  with replacement: {r.pairs.mean():,.0f} pairs, {r.distinct.mean():,.0f} distinct "
          f"controls, largest reuse {r.max_reuse.mean():.1f} on average")
    for k in ("odds", "ipw_ate"):
        q = t[t.estimator == k]
        print(f"  {LABELS[k]}: weighted regression default {q.se_wls_default.mean() / sp[k]:.2f}, "
              f"frequency convention {q.se_wls_freq.mean() / sp[k]:.2f}, robust "
              f"{q.se_wls_robust.mean() / sp[k]:.2f}")

    banner(f"Table 9.3 - what a 95 per cent interval covers, {nd} draws")
    print(f"  {'':34s} {'SE used':>14s} {'Bias':>7s} {'Bias/SE':>8s} {'Covers truth':>13s} {'Covers own mean':>16s}")
    rows = [(k, RECOMMENDED[k]) for k in ORDER] + [("odds", "se_naive")]
    for k, m in rows:
        q = t[(t.estimator == k)].dropna(subset=[m])
        mu = q.err.mean()
        cov = (np.abs(q.err) <= 1.96 * q[m]).mean()
        cen = (np.abs(q.err - mu) <= 1.96 * q[m]).mean()
        name = dict(METHODS)[m]
        print(f"  {LABELS[k]:34s} {name:>14s} {q.bias.mean():+6.1f}% {mu / q[m].mean():+8.1f} "
              f"{100 * cov:12.0f}% {100 * cen:15.0f}%   ({len(q)} draws)")

    if nd < 12:
        return
    banner(f"Table 9.4 - the book's six draws against {nd}")
    w = t.pivot(index="seed", columns="estimator", values="bias")
    six = w.iloc[:6]
    print(f"  {'':34s} {'Six: mean':>10s} {'sd':>6s} {f'{nd}: mean':>10s} {'sd':>6s} {'Rank of six':>12s}")
    blocks = w.iloc[: 6 * (nd // 6)].groupby(np.arange(6 * (nd // 6)) // 6).mean()
    for k in ["odds", "dr_att", "sub20", "sub20_reg", "match", "maha", "maha13", "ipw_ate"]:
        rank = int((blocks[k] < blocks[k].iloc[0]).sum()) + 1
        print(f"  {LABELS[k]:34s} {six[k].mean():+9.1f}% {six[k].std():6.1f} {w[k].mean():+9.1f}% "
              f"{w[k].std():6.1f} {rank:>5d} of {len(blocks)}")
    print(f"  standard error of a {nd}-draw mean bias: "
          + ", ".join(f"{LABELS[k]} {w[k].std() / np.sqrt(nd):.2f}" for k in ("odds", "match", "maha")))

    banner(f"Table 9.5 - comparing two designs on the same draws, {nd} draws")
    print(f"  {'':52s} {'Mean':>7s} {'sd of':>7s} {'sd of':>7s} {'Same':>6s} {'SE of diff':>11s}")
    print(f"  {'':52s} {'diff':>7s} {'diff':>7s} {'each':>7s} {'sign':>6s} {'if unpaired':>11s}")
    pairs = [("match", "maha"), ("maha13", "maha"), ("sub20_reg", "sub20"),
             ("dr_att", "odds"), ("match_repl", "match")]
    se = t.pivot(index="seed", columns="estimator", values="truth")
    for a_, b_ in pairs:
        d = w[a_] - w[b_]
        each = (w[a_].std() + w[b_].std()) / 2
        unp = np.sqrt(w[a_].std() ** 2 + w[b_].std() ** 2)
        same = (np.sign(d) == np.sign(d.mean())).mean()
        print(f"  {LABELS[a_] + ' less ' + LABELS[b_]:52s} {d.mean():+7.1f} {d.std():7.1f} {each:7.1f} "
              f"{100 * same:5.0f}% {unp:11.1f}")
    print("  all in percentage points of the true ATT")
    rmse = {k: np.sqrt((w[k] ** 2).mean()) for k in ("maha", "maha13")}
    print(f"  root mean squared error: Mahalanobis 1:1 {rmse['maha']:.1f}, 1:3 {rmse['maha13']:.1f}")

    if nd >= 40:
        figure(t, sp, sp_b, outdir)


def figure(t, sp, sp_b, outdir):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.linewidth": 0.8,
                         "axes.labelsize": 8.5, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
                         "legend.fontsize": 7.5, "legend.frameon": False, "savefig.dpi": 300,
                         "savefig.bbox": "tight", "savefig.facecolor": "white"})
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.9, 3.4), gridspec_kw={"width_ratios": [1.05, 1]})
    shown = ["odds", "ipw_ate", "sub20", "dr_att", "match", "match_repl", "maha"]
    naive = {"odds": "se_naive", "ipw_ate": "se_naive", "sub20": "se_naive", "dr_att": "se_naive",
             "match": "se_paired", "match_repl": "se_paired", "maha": "se_paired"}
    for j, k in enumerate(shown):
        q = t[t.estimator == k]
        yj = len(shown) - 1 - j
        nv = q[naive[k]].mean() / sp[k]
        m = RECOMMENDED[k]
        rc = q[m].mean() / (sp_b[k] if m == "se_boot" else sp[k])
        a1.plot([nv, rc], [yj, yj], color="black", linewidth=0.6)
        a1.scatter([nv], [yj], s=22, facecolors="white", edgecolors="black", zorder=3,
                   label="as quoted in Chapters 5 to 7" if j == 0 else None)
        a1.scatter([rc], [yj], s=22, marker="s", color="black", zorder=3,
                   label="recommended in Section 9.9" if j == 0 else None)
    a1.axvline(1, color="black", linewidth=0.7, linestyle=(0, (1, 2)))
    a1.set_yticks(range(len(shown)))
    a1.set_yticklabels([LABELS[k] for k in reversed(shown)])
    a1.set_xlabel("Standard error / actual spread")
    a1.legend(loc="lower right", handletextpad=0.3)
    q = t[t.estimator == "odds"].sort_values("seed").head(40)
    b = 100 * q.err.values / q.truth.values
    h = 100 * 1.96 * q.se_sandwich.values / q.truth.values
    x = np.arange(len(q))
    covers = np.abs(b) <= h
    for i in x:
        a2.plot([i, i], [b[i] - h[i], b[i] + h[i]], color="black" if covers[i] else "0.6",
                linewidth=0.9)
    a2.scatter(x, b, s=6, color="black", zorder=3)
    a2.axhline(0, color="black", linewidth=0.8, label="truth")
    a2.axhline(b.mean(), color="black", linewidth=0.7, linestyle=(0, (4, 2)),
               label="mean of the estimates")
    a2.plot([], [], color="black", linewidth=0.9, label="interval contains the truth")
    a2.plot([], [], color="0.6", linewidth=0.9, label="interval misses the truth")
    a2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, handlelength=1.8)
    a2.set_xlabel("Draw")
    a2.set_ylabel("Error, % of the true ATT")
    a2.set_xticks([0, 9, 19, 29, 39])
    a2.set_xticklabels(["1", "10", "20", "30", "40"])
    for ax, letter in ((a1, "a"), (a2, "b")):
        for sp_ in ("top", "right"):
            ax.spines[sp_].set_visible(False)
        ax.text(-0.02, 1.04, f"({letter})", transform=ax.transAxes, fontsize=10,
                fontweight="bold", va="bottom", ha="right")
    fig.subplots_adjust(wspace=0.55)
    for ext in ("tif", "png"):
        fig.savefig(outdir / f"figure_9_1_standard_errors.{ext}")
    print(f"\n  wrote figure_9_1_standard_errors.tif to {outdir}")
    print(f"  panel (b): {int(covers.sum())} of {len(q)} intervals contain the truth")


if __name__ == "__main__":
    main()
