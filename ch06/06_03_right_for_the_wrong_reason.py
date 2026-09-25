#!/usr/bin/env python3
"""
Script 6.3 — Right for the wrong reason
========================================
Chapter 6, the box in Section 6.9. Produces Table 6.7.

Uses truth_parameters.csv beyond the true effect, which no analysis in the book
may do. It reads the generator's true propensity score and its two unmeasured
confounders, earnings_shock_2016 and u_employability, to explain a result: why
a plain outcome regression recovers the ATT almost exactly when every
propensity score method is about twelve per cent low. Nothing here is a method
a reader could use on real data; it is a diagnosis only a simulation permits.

It generates its own draws, the six of Chapter 5, and ignores --datadir.

    python ch06/06_03_right_for_the_wrong_reason.py
"""
import sys, subprocess, tempfile
import atexit, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _common6 import (cli, banner, score, REPO, att_weights, att_odds,
                      outcome_design, outcome_fits, att_regression, pct)
import numpy as np, pandas as pd

sys.path.insert(0, str(REPO / "ch03"))
from _common3 import fit_propensity                                     # noqa: E402

SEEDS = [20260808, 20260809, 20260810, 20260811, 20260812, 20260813]
HIDDEN = ["earnings_shock_2016", "u_employability"]


def one_draw(seed, tmp):
    out = tmp / f"d{seed}"
    subprocess.run([sys.executable, str(REPO / "make_data.py"), "--seed", str(seed),
                    "--n", "50000", "--outdir", str(out), "--quiet"], check=True)
    for s in ("ch02/02_05_link_modules.py", "ch02/02_06_reshape_panel.py"):
        subprocess.run([sys.executable, str(REPO / s), "--datadir", str(out)],
                       check=True, capture_output=True)
    sc = score(out, "logit", with_truth=True)
    E, X, D, ps, y, tau = sc["E"], sc["X"], sc["D"], sc["ps"], sc["y"], sc["tau"]
    tp = (pd.read_csv(out / "truth" / "truth_parameters.csv")
          .set_index("person_id").reindex(E.index))
    U = tp[HIDDEN].set_index(X.index)
    att = tau[D == 1].mean()
    XU = pd.concat([X, U], axis=1)
    ps_u = fit_propensity(XU, D, "logit")
    ps_true = tp["true_propensity"].values
    Q = outcome_design(E, X)
    QU = pd.concat([Q, U], axis=1)
    _, m0 = outcome_fits(Q, D, y)
    _, m0u = outcome_fits(QU, D, y)
    return dict(
        seed=seed,
        odds_reader=pct(att_odds(D, y, att_weights(ps, D)), att),
        odds_true=pct(att_odds(D, y, att_weights(ps_true, D)), att),
        odds_hidden=pct(att_odds(D, y, att_weights(ps_u, D)), att),
        reg_reader=pct(att_regression(D, y, m0), att),
        reg_hidden=pct(att_regression(D, y, m0u), att),
        corr_true=np.corrcoef(ps, ps_true)[0, 1],
        smd_shock=(U.iloc[:, 0][D == 1].mean() - U.iloc[:, 0][D == 0].mean()) / U.iloc[:, 0].std(),
        smd_u=(U.iloc[:, 1][D == 1].mean() - U.iloc[:, 1][D == 0].mean()) / U.iloc[:, 1].std(),
    )


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
    a.outdir.mkdir(parents=True, exist_ok=True)
    t.to_csv(a.outdir / "wrong_reason_results.csv")
    m, sd = t.mean(), t.std()

    banner(f"Table 6.7 - right for the wrong reason, {len(seeds)} draw(s)")
    print(f"  {'':52s} {'Bias':>8s} {'sd':>6s}")
    for lab, k in (("Odds weighting, the reader's score", "odds_reader"),
                   ("Odds weighting, the true propensity score", "odds_true"),
                   ("Odds weighting, both hidden confounders added", "odds_hidden"),
                   ("Outcome regression, the reader's covariates", "reg_reader"),
                   ("Outcome regression, both hidden confounders added", "reg_hidden")):
        s_ = "-" if np.isnan(sd[k]) else f"{sd[k]:.1f}"
        print(f"  {lab:52s} {m[k]:+7.1f}% {s_:>6s}")
    print(f"\n  the reader's score correlates with the true score at {m.corr_true:.2f}")
    print(f"  hidden confounders, treated less controls (standardised): "
          f"earnings shock {m.smd_shock:+.2f}, employability {m.smd_u:+.2f}")
    print("\n  Weighting by the true score removes the bias. The reader's score misses")
    print("  the two confounders and part of the functional form. The regression's")
    print("  accuracy is a cancellation: given the confounders it moves away from zero.")


if __name__ == "__main__":
    main()
