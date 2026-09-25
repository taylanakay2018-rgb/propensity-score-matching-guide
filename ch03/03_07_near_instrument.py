#!/usr/bin/env python3
"""
Script 3.7 — What a near-instrument costs
==========================================
Chapter 3, Section 3.7. Produces Table 3.5.

Adds mutual_obligation_status to the propensity model and measures what is
purchased with the improvement in predictive performance. The answer is best
read on the effective sample size row.

This script generates its own draws and ignores --datadir.

    python ch03/03_07_near_instrument.py
    python ch03/03_07_near_instrument.py --quick
"""
import sys, subprocess, tempfile
import atexit, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _common3 import (cli, banner, load_analysis, design_matrix, eligible_only,
                      fit_propensity, stabilised_weights, effective_n, match,
                      matched_bias, REPO)
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score

SEEDS = [20260808, 20260809, 20260810, 20260811, 20260812]


def odds_weighted_att(ps, D, y):
    """The ATT by odds weighting, which Chapter 6 develops properly."""
    w = np.where(D == 1, 1.0, ps / (1 - ps))
    c_mean = np.average(y[D == 0], weights=w[D == 0])
    t_mean = y[D == 1].mean()
    est = t_mean - c_mean
    # Treated term centred on the treated mean (v5.0); see Section 6.10.
    psi = (D * (y - t_mean) - (1 - D) * w * (y - c_mean)) / D.mean()
    return est, psi.std(ddof=1) / np.sqrt(len(y)), w


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
    r = {"seed": seed}
    for lab, Xs in [("without", X), ("with", pd.concat([X, MO], axis=1))]:
        ps = fit_propensity(Xs, D, "logit")
        est, se, w = odds_weighted_att(ps, D, y)
        mt, mc, un = match(ps, D)
        bias, _, _ = matched_bias(mt, mc, y, tau)
        r[f"auc_{lab}"] = roc_auc_score(D, ps)
        r[f"stabmax_{lab}"] = stabilised_weights(ps, D).max()
        r[f"oddsmax_{lab}"] = w[D == 0].max()
        r[f"ess_{lab}"] = effective_n(w[D == 0])
        r[f"se_{lab}"] = se
        r[f"unmatched_{lab}"] = un
        r[f"bias_{lab}"] = bias
    return r


def main():
    a = cli(__doc__)
    seeds = SEEDS[:1] if a.quick else SEEDS
    tmp = Path(tempfile.mkdtemp())
    atexit.register(shutil.rmtree, tmp, ignore_errors=True)   # leave no draws behind
    rows = []
    for s in seeds:
        rows.append(one_draw(s, tmp))
        print(f"  draw {s} done", file=sys.stderr, flush=True)
    t = pd.DataFrame(rows).set_index("seed")
    # Saved so that audit.py can hold Table 3.5 to the draws.
    a.outdir.mkdir(parents=True, exist_ok=True)
    t.to_csv(a.outdir / "near_instrument_results.csv")
    m = t.mean()
    sd = t.std()

    banner(f"Table 3.5 - the cost of adding the near-instrument, {len(seeds)} draw(s)")
    rows_out = [("Area under the ROC curve", "auc", "{:.3f}"),
                ("Largest stabilised weight", "stabmax", "{:.1f}"),
                ("Largest control odds weight", "oddsmax", "{:.1f}"),
                ("Effective control sample size", "ess", "{:,.0f}"),
                ("Standard error, weighted estimate", "se", "{:.0f}"),
                ("Treated left unmatched", "unmatched", "{:,.0f}"),
                ("Bias of the matched estimate (%)", "bias", "{:+.1f}")]
    print(f"  {'':36s} {'Without':>12s} {'With':>12s}")
    for label, key, fmt in rows_out:
        print(f"  {label:36s} {fmt.format(m[f'{key}_without']):>12s} "
              f"{fmt.format(m[f'{key}_with']):>12s}")
    if len(seeds) > 1:
        print(f"  {'sd of that bias':36s} {sd['bias_without']:>12.1f} "
              f"{sd['bias_with']:>12.1f}")
    print(f"\n  The largest stabilised weight rises {m['stabmax_with']/m['stabmax_without']:.1f}"
          f" times and the standard error by "
          f"{100*(m['se_with']/m['se_without']-1):.0f} per cent.")
    print(f"  {100*(1-m['ess_with']/m['ess_without']):.0f} per cent of the control"
          " information is spent on a covariate that removes no bias.")
    print("\n  The bias row shows no reliable change. The covariate costs precision")
    print("  and buys nothing dependable, which is the theoretical prediction.")


if __name__ == "__main__":
    main()
