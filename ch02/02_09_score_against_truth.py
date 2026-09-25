#!/usr/bin/env python3
"""
Script 2.9 — Score the preparation decisions against truth
===========================================================
Chapter 2, Section 2.9.3. Produces Table 2.9.

Prices each preparation failure in two currencies: damage to the estimate,
and damage to the estimand. Repeats every comparison across five independent
draws, because a single draw cannot separate the two.

This script joins truth_parameters.csv. No analysis in the book may.

    python ch02/02_09_score_against_truth.py            # five draws, ~4 min
    python ch02/02_09_score_against_truth.py --quick    # one draw
"""
import sys, subprocess, tempfile
import atexit, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _common import cli, load, banner, deflate, BASELINE_YEAR
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer
from sklearn.neighbors import NearestNeighbors

B = BASELINE_YEAR
REPO = Path(__file__).resolve().parent.parent
SEEDS = [20260808, 20260809, 20260810, 20260811, 20260812]


def build(datadir):
    d = load(datadir, with_truth=True)
    t = d["truth"].set_index("person_id")
    inc = deflate(d["pit_income"], d["reference_indices"], ["salary_wages_nominal"])
    w = inc.pivot_table(index="person_id", columns="ref_year",
                        values="salary_wages_real").reindex(t.index)
    cen = d["census16_person"].set_index("person_id").reindex(t.index)
    loc = d["core_locations"].query("ref_year == @B").set_index("person_id").reindex(t.index)
    hl = d["mbs_pbs_health"].query("ref_year == @B").set_index("person_id").reindex(t.index)
    dom = d["domino_payments"].query("ref_year == @B")
    fn = dom.groupby("person_id")["fortnights_on_payment"].sum().reindex(t.index).fillna(0)
    mo = (dom.sort_values("fortnights_on_payment", ascending=False).drop_duplicates("person_id")
          .set_index("person_id")["mutual_obligation_status"].reindex(t.index).fillna("Exempt"))
    edu = {"<Year 12": 0, "Year 12": 1, "Cert III/IV": 2, "Diploma": 3, "Bachelor+": 4}
    rem = {"Major Cities": 0, "Inner Regional": 1, "Outer Regional": 2, "Remote+": 3}
    X = pd.DataFrame({
        "age": B - d["core_demographics"].set_index("person_id").reindex(t.index)["birth_year"],
        "log_inc_2015": np.log1p(w[2015]), "log_inc_2016": np.log1p(w[2016]),
        "fn_2016": fn, "lts": (fn >= 20).astype(int),
        "gp": hl["gp_attendances"].fillna(0), "mh": hl["mh_item_flag"].fillna(0),
        "edu": cen["highest_edu"].map(edu), "kids": cen["dependent_children"],
        "lang": cen["english_proficiency"].map({"Not well": 1, "Well": 0}),
        "remote": loc["remoteness_area"].map(rem), "seifa": loc["seifa_irsd_decile"],
        "mo_intensive": (mo == "Intensive").astype(int), "mo_full": (mo == "Full").astype(int),
        "mo_partial": (mo == "Partial").astype(int),
    }, index=t.index)
    y = np.where(t["treated"] == 1, t["y1"], t["y0"]).astype(float)
    left = (d["spine_scoping"].set_index("person_id").reindex(t.index)["last_active_year"] < 2019).values
    present = {m: set(d[m].query("ref_year == @B").person_id) if "ref_year" in d[m] else set(d[m].person_id)
               for m in ("pit_income", "census16_person", "mbs_pbs_health")}
    inner = np.array([all(p in present[m] for m in present) for p in t.index])
    return X, t["treated"].values, y, t["tau_i"].values, left, inner


def att(X, D, y, tau, ref):
    """1:1 nearest-neighbour match, 0.1 SD caliper. Returns (local bias, bias vs ref)."""
    X = X.copy()
    for c in X.columns:
        X[c] = X[c].fillna(X[c].median())
    Xs = (X - X.mean()) / X.std().replace(0, 1)
    ps = LogisticRegression(max_iter=4000, C=1e6).fit(Xs, D).predict_proba(Xs)[:, 1]
    lo = np.log(ps / (1 - ps))
    t_, c_ = np.where(D == 1)[0], np.where(D == 0)[0]
    nn = NearestNeighbors(n_neighbors=1).fit(lo[c_].reshape(-1, 1))
    dd, ii = nn.kneighbors(lo[t_].reshape(-1, 1))
    k = dd.ravel() <= 0.1 * lo.std()
    mt, mc = t_[k], c_[ii.ravel()[k]]
    est = (y[mt] - y[mc]).mean()
    return 100 * (est - tau[mt].mean()) / tau[mt].mean(), 100 * (est - ref) / ref


def one_draw(datadir):
    X, D, y, tau, left, inner = build(datadir)
    ATT = tau[D == 1].mean()
    r = {}
    r["correct"], _ = att(X, D, y, tau, ATT)
    drop = [c for c in X.columns if X[c].isna().any()]
    r["drop_columns"], _ = att(X.drop(columns=drop), D, y, tau, ATT)
    cc = X.notna().all(axis=1).values
    r["complete_case"], r["complete_case_policy"] = att(X[cc], D[cc], y[cc], tau[cc], ATT)
    r["inner_join"], r["inner_join_policy"] = att(X[inner], D[inner], y[inner], tau[inner], ATT)
    sv = ~left
    r["survivors"], r["survivors_policy"] = att(X[sv], D[sv], y[sv], tau[sv], ATT)
    r["retained_inner"] = 100 * inner.mean()
    r["retained_cc"] = 100 * cc.mean()
    r["retained_sv"] = 100 * sv.mean()
    return r


def main():
    a = cli(__doc__)
    quick = "--quick" in sys.argv
    seeds = SEEDS[:1] if quick else SEEDS
    rows = []
    tmp = Path(tempfile.mkdtemp())
    atexit.register(shutil.rmtree, tmp, ignore_errors=True)   # leave no draws behind
    for i, seed in enumerate(seeds):
        if i == 0 and a.datadir.exists():
            dd = a.datadir
        else:
            dd = tmp / f"draw_{seed}"
            subprocess.run([sys.executable, str(REPO / "make_data.py"),
                            "--seed", str(seed), "--outdir", str(dd), "--quiet"], check=True)
        print(f"  draw {seed} ...", file=sys.stderr)
        rows.append(one_draw(dd))
    t = pd.DataFrame(rows)

    banner("Table 2.9 — what each preparation failure costs")
    print(f"  {'Failure':38s} {'Estimate':>12s} {'Estimand':>22s}")
    print(f"  {'Drop columns containing any missing':38s} {t.drop_columns.mean():>11.0f}% "
          f"{'none':>22s}")
    print(f"  {'Chain inner joins':38s} {t.inner_join_policy.mean()-t.correct.mean():>10.1f}pp "
          f"{100-t.retained_inner.mean():>19.1f}% removed")
    print(f"  {'Complete-case analysis':38s} {t.complete_case_policy.mean()-t.correct.mean():>10.1f}pp "
          f"{100-t.retained_cc.mean():>19.1f}% removed")
    print(f"  {'Ignore attrition':38s} {t.survivors_policy.mean()-t.correct.mean():>10.1f}pp "
          f"{100-t.retained_sv.mean():>19.1f}% removed")
    print(f"\n  correct build, for reference: {t.correct.mean():+.1f}% "
          f"(sd {t.correct.std():.1f} across {len(t)} draws)")
    if len(t) > 1:
        banner("Spread across draws — why one draw cannot settle this")
        print(pd.DataFrame({"mean": t.mean(), "sd": t.std()}).round(2).to_string())
    print("\n  Only the first failure produces a large, reliable, detectable bias.")
    print("  The rest leave the estimate roughly where it was and change the")
    print("  population it describes. See Section 2.9.3.")

if __name__ == "__main__":
    main()
