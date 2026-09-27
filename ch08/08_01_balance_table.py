#!/usr/bin/env python3
"""
Script 8.1 — Balance on the primary dataset
============================================
Chapter 8, Sections 8.3 to 8.5. Produces Tables 8.1, 8.2 and 8.3.

On the primary dataset and the logistic score of Chapter 3: the balance table
for the propensity score matched sample, built with causalml's
create_table_one and with the fixed-denominator function of Fragment 8.1;
the diagnostics beyond the mean for five adjusted samples; and balance on
the pre-programme variables the propensity model does not use. None of this
reads the outcome or the truth file.

    python ch08/08_01_balance_table.py
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common8 import (cli, banner, score, adjusted_samples, diagnostics, summary,
                      constructed_terms, held_out_matrix, pooled_sd, smd, LABELS, HELD_OUT,
                      HELD_OUT_NUMERIC)
import numpy as np, pandas as pd

TABLE_8_2 = ["Unadjusted", "Propensity score matching", "Mahalanobis matching",
             "Odds weighting", "Subclassification, 5 strata", "Subclassification, 20 strata"]


def table_8_1(X, D, wt, wc):
    """Means and standardised differences before and after matching."""
    from causalml.match import create_table_one
    t, c = np.repeat(np.arange(len(D)), wt.astype(int)), np.repeat(np.arange(len(D)), wc.astype(int))
    matched = pd.concat([X.iloc[t].assign(treated=1), X.iloc[c].assign(treated=0)])
    before = create_table_one(X.assign(treated=D), "treated", list(X.columns))
    after = create_table_one(matched, "treated", list(X.columns))
    V = X.values.astype(float)
    fixed = pd.Series(smd(V, wt, wc, pooled_sd(V, D)), X.columns)
    rows = []
    for col in X.columns:
        rows.append(dict(covariate=col, treated=X[col][D == 1].mean(),
                         control_before=X[col][D == 0].mean(),
                         smd_before=float(before.loc[col, "SMD"]),
                         control_after=np.average(X[col], weights=wc),
                         smd_after=float(after.loc[col, "SMD"]),
                         smd_after_fixed=float(fixed[col])))
    return pd.DataFrame(rows).set_index("covariate"), int(wt.sum())


def table_8_3(E, D, wt, wc):
    """Largest standardised difference within each held-out variable."""
    H = held_out_matrix(E)
    Hv = H.values
    sd = pooled_sd(Hv, D)
    before = pd.Series(smd(Hv, (D == 1) * 1.0, (D == 0) * 1.0, sd), H.columns).abs()
    after = pd.Series(smd(Hv, wt, wc, sd), H.columns).abs()
    rows = []
    for v in HELD_OUT + HELD_OUT_NUMERIC:
        cols = [c for c in H.columns if c == v or c.startswith(v + "_")]
        rows.append(dict(variable=v, before=before[cols].max(), after=after[cols].max(),
                         worst="" if v in HELD_OUT_NUMERIC else after[cols].idxmax().replace(v + "_", "")))
    return pd.DataFrame(rows).set_index("variable")


def main():
    a = cli(__doc__)
    sc = score(a.datadir, "logit")
    E, X, D, ps = sc["E"], sc["X"], sc["D"], sc["ps"]
    S = adjusted_samples(X, D, ps, strata=(5, 20))
    wt, wc = S["Propensity score matching"]

    banner("Table 8.1 - a balance table, before and after propensity score matching")
    t1, pairs = table_8_1(X, D, wt, wc)
    print(f"  {'':24s} {'Treated':>9s} {'Control':>9s} {'SMD':>7s} {'Control':>9s} {'SMD':>7s} {'SMD, fixed':>11s}")
    print(f"  {'':24s} {'':>9s} {'before':>9s} {'before':>7s} {'after':>9s} {'after':>7s} {'denominator':>11s}")
    for c, r in t1.iterrows():
        print(f"  {LABELS[c]:24s} {r.treated:9.3f} {r.control_before:9.3f} {r.smd_before:+7.3f} "
              f"{r.control_after:9.3f} {r.smd_after:+7.3f} {r.smd_after_fixed:+11.3f}")
    print(f"\n  treated {int(D.sum()):,}; controls {int((D == 0).sum()):,}; matched pairs {pairs:,}")
    gap = (t1.smd_after - t1.smd_after_fixed).abs()
    print(f"  largest gap between the two denominators after matching: {gap.max():.4f} "
          f"({LABELS[gap.idxmax()]})")
    print(f"  covariates above 0.1 before: {int((t1.smd_before.abs() > 0.1).sum())} of {len(t1)}; "
          f"after: {int((t1.smd_after.abs() > 0.1).sum())}")

    banner("Table 8.2 - diagnostics beyond the mean, primary dataset")
    C = constructed_terms(X)
    rows = {k: summary(diagnostics(X, D, *S[k], C=C)) for k in TABLE_8_2}
    print(f"  {'':30s} {'Largest':>8s} {'VR out of':>10s} {'Most':>7s} {'Largest':>8s} {'Largest':>9s} {'Terms':>6s}")
    print(f"  {'':30s} {'SMD':>8s} {'0.8-1.25':>10s} {'extreme':>7s} {'KS':>8s} {'term SMD':>9s} {'> 0.1':>6s}")
    for k, r in rows.items():
        print(f"  {k:30s} {r['smd_max']:8.3f} {r['vr_out']:10d} {r['vr_extreme']:7.2f} "
              f"{r['ks_max']:8.3f} {r['con_max']:9.3f} {r['con_over_01']:6d}")
    print(f"  constructed terms: {rows['Unadjusted']['con_n']} (squares of the non-binary "
          f"covariates and every pairwise product)")
    d = diagnostics(X, D, *S["Propensity score matching"])
    print(f"  propensity score matching, variance ratios run from {d['vr'].min():.2f} "
          f"to {d['vr'].max():.2f}")

    banner("Table 8.3 - balance on variables the propensity model does not use")
    t3 = table_8_3(E, D, wt, wc)
    print(f"  {'':28s} {'Before':>8s} {'After matching':>15s}   worst category after")
    for v, r in t3.iterrows():
        print(f"  {v:28s} {r.before:8.3f} {r.after:15.3f}   {r.worst}")


if __name__ == "__main__":
    main()
