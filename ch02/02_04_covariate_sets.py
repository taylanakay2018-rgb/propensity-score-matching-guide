#!/usr/bin/env python3
"""
Script 2.4 — The covariate taxonomy
====================================
Chapter 2, Section 2.4. Produces Tables 2.1 and 2.2.

For each candidate covariate, how well it discriminates on treatment and how
much of the untreated outcome it explains. Confounders score on both; a pure
outcome predictor scores on the second only; a near-instrument on the first
only. The table cannot settle the classification — see Section 2.4.1 — but it
shows what the categories look like.

    python ch02/02_04_covariate_sets.py
    python ch02/02_04_covariate_sets.py --placement   # adds Table 2.2, ~4 min
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common import (cli, load, banner, deflate, BASELINE_YEAR,
                     occupation_carried_forward, mutual_obligation_dominant)
import numpy as np, pandas as pd
from pathlib import Path
from _common import REPO
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import roc_auc_score

# Declared before any model is fitted. See Fragment 2.1.
CONFOUNDERS = ["fortnights_2016", "log_earnings_2016", "log_earnings_2015",
               "highest_edu", "remoteness", "seifa", "mh_item_flag",
               "gp_attendances", "age", "dependent_children"]
OUTCOME_ONLY = ["occupation_group"]
TREATMENT_ONLY = ["mutual_obligation_status"]


def table_2_2(a):
    """Table 2.2 - where a pure outcome predictor earns its keep.

    Section 2.4.2. A covariate that predicts the outcome but not treatment is
    worth including, but only in the model of the outcome. Adding it to the
    propensity model instead does nothing useful, and this is the experiment
    that shows it: occupation is added in each place in turn, across six
    independent draws, and the standard error is compared with the same
    estimator fitted without it.

    Six draws are generated here rather than read from disk, because a single
    draw cannot separate a one per cent precision gain from sampling noise.
    """
    import subprocess, tempfile
    import atexit, shutil
    from sklearn.neighbors import NearestNeighbors
    sys.path.insert(0, str(REPO))
    import validate_data as VD

    banner("Table 2.2 - what a pure outcome predictor buys, by placement")
    rows = []
    tmp = Path(tempfile.mkdtemp())
    atexit.register(shutil.rmtree, tmp, ignore_errors=True)   # leave no draws behind
    for seed in (20260808, 20260809, 20260810, 20260811, 20260812, 20260813):
        out = tmp / f"d{seed}"
        subprocess.run([sys.executable, str(REPO / "make_data.py"), "--seed", str(seed),
                        "--n", "50000", "--outdir", str(out), "--quiet"], check=True)
        dd = VD.load(out)
        df = VD.assemble(dd)
        X = VD.design_matrix(df)
        X = X.fillna(X.median())
        occ_s = occupation_carried_forward(dd["pit_income"]).reindex(df.index).fillna("None")
        O = pd.get_dummies(occ_s, prefix="occ", drop_first=True).astype(float)
        O.index = X.index
        D = df.treated.values
        y = np.where(D == 1, df.y1, df.y0)
        tau = df.tau_i.values

        def matched(Xd):
            Z = (Xd - Xd.mean()) / Xd.std().replace(0, 1)
            ps = LogisticRegression(max_iter=4000, C=1e6).fit(Z, D).predict_proba(Z)[:, 1]
            lo = np.log(ps / (1 - ps))
            t_i, c_i = np.where(D == 1)[0], np.where(D == 0)[0]
            nn = NearestNeighbors(n_neighbors=1).fit(lo[c_i].reshape(-1, 1))
            dist, idx = nn.kneighbors(lo[t_i].reshape(-1, 1))
            k = dist.ravel() <= 0.1 * lo.std()
            mt, mc = t_i[k], c_i[idx.ravel()[k]]
            diff = y[mt] - y[mc]
            return diff.std(ddof=1) / np.sqrt(len(diff)), ps

        se_base, ps = matched(X)
        se_ps, _ = matched(pd.concat([X, O], axis=1))

        def aipw_se(Xout):                      # occupation in the outcome model
            m0 = LinearRegression().fit(Xout[D == 0], y[D == 0]).predict(Xout)
            m1 = LinearRegression().fit(Xout[D == 1], y[D == 1]).predict(Xout)
            pc, w = np.clip(ps, .01, .99), D.mean()
            psi = (D * (y - m1) / pc - (1 - D) * (y - m0) / (1 - pc)) * pc / w + (m1 - m0) * pc / w
            return psi.std(ddof=1) / np.sqrt(len(psi))

        rows.append({"seed": seed,
                     "propensity model": se_ps / se_base,
                     "outcome model": aipw_se(pd.concat([X, O], axis=1)) / aipw_se(X)})
        print(f"  seed {seed} done", file=sys.stderr, flush=True)

    t = pd.DataFrame(rows).set_index("seed")
    print(f"  {'Where it is added':32s} {'SE ratio':>9s} {'Draws improved':>16s}")
    for col, label in [("propensity model", "Propensity model, then matched"),
                       ("outcome model", "Outcome model, doubly robust")]:
        print(f"  {label:32s} {t[col].mean():9.3f} {f'{(t[col] < 1).sum()} of {len(t)}':>16s}")
    print("\n  Below one is an improvement. Only one placement delivers it.")


def main():
    a = cli(__doc__)
    d = load(a.datadir, with_truth=True)
    t = d["truth"].set_index("person_id")
    D, y0 = t["treated"].values, t["y0"].values

    inc = deflate(d["pit_income"], d["reference_indices"], ["salary_wages_nominal"])
    w = inc.pivot_table(index="person_id", columns="ref_year",
                        values="salary_wages_real").reindex(t.index)
    cen = d["census16_person"].set_index("person_id").reindex(t.index)
    loc = (d["core_locations"].query("ref_year == @BASELINE_YEAR")
           .set_index("person_id").reindex(t.index))
    hl = (d["mbs_pbs_health"].query("ref_year == @BASELINE_YEAR")
          .set_index("person_id").reindex(t.index))
    dom = d["domino_payments"].query("ref_year == @BASELINE_YEAR")
    fn = dom.groupby("person_id")["fortnights_on_payment"].sum().reindex(t.index).fillna(0)
    # Persons with no 2016 payment row get their own level rather than being
    # folded into "Exempt"; see mutual_obligation_dominant and Section 2.5.2.
    mo = mutual_obligation_dominant(dom, index=t.index)
    # Carried forward from the most recent pre-period year in which it is
    # observed, not taken from 2016 alone. See Section 2.6.3: reading it from
    # the treatment year would make "None" an exact copy of the 2016
    # non-lodgement indicator, and so import Section 2.7's missingness
    # mechanism into a variable the chapter offers as clean.
    occ = occupation_carried_forward(d["pit_income"]).reindex(t.index).fillna("None")
    prog = d["epp_program"].set_index("person_id")

    def score(X):
        X = np.asarray(X, dtype=float)
        if X.ndim == 1: X = X[:, None]
        ok = ~np.isnan(X).any(1)
        auc = roc_auc_score(D[ok], LogisticRegression(max_iter=2000)
                            .fit(X[ok], D[ok]).predict_proba(X[ok])[:, 1])
        r2 = LinearRegression().fit(X[ok], y0[ok]).score(X[ok], y0[ok])
        return auc, r2

    edu_order = {"<Year 12": 0, "Year 12": 1, "Cert III/IV": 2, "Diploma": 3, "Bachelor+": 4}
    candidates = [
        ("Earnings in 2016", "True confounder", np.log1p(w[2016])),
        ("Highest education", "True confounder", cen["highest_edu"].map(edu_order)),
        ("Fortnights on payment, 2016", "True confounder", fn),
        ("occupation_group", "Pure outcome predictor", pd.get_dummies(occ).astype(float)),
        ("mutual_obligation_status", "Near-instrument", pd.get_dummies(mo).astype(float)),
        ("Remoteness", "?", loc["remoteness_area"].map(
            {"Major Cities": 0, "Inner Regional": 1, "Outer Regional": 2, "Remote+": 3})),
        ("Mental health item flag", "?", hl["mh_item_flag"].fillna(0)),
    ]
    banner("Table 2.1 — the covariate taxonomy")
    print(f"  {'Variable':30s} {'Expected kind':24s} {'Discrim.':>9s} {'Outcome':>9s}")
    for name, kind, X in candidates:
        auc, r2 = score(X)
        print(f"  {name:30s} {kind:24s} {auc:9.3f} {r2:9.3f}")
    trap = t.index.isin(prog.index).astype(float)
    print(f"  {'referral_type':30s} {'Post-treatment':24s} {1.000:9.3f} {'—':>9s}")

    print("\n  referral_type is observed only for participants, so it predicts")
    print("  treatment perfectly and will separate any model that uses it.")
    print(f"  Perfect predictor check: {bool((trap == D).all())}")

    if a.placement:
        table_2_2(a)

    banner("Declared covariate sets (Fragment 2.1)")
    for label, s in [("confounders", CONFOUNDERS), ("outcome only", OUTCOME_ONLY),
                     ("treatment only", TREATMENT_ONLY)]:
        print(f"  {label:16s} {', '.join(s)}")

if __name__ == "__main__":
    main()
