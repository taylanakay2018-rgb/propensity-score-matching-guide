#!/usr/bin/env python3
"""
PLIDA-SIM validator
===================

Rebuilds the analysis dataset the way a reader is meant to -- linking the
modules through the spine, deflating to constant 2019 dollars, collapsing the
panel to one row per person -- then reproduces every benchmark number quoted in
the design specification and checks it against target.

Two jobs:

1.  Confirm the generator implements the spec.
2.  Serve as the repository's CI check.  If a library upgrade changes a result,
    this fails before a reader finds it.

Usage
-----
    python validate_data.py --datadir plida_sim_a
    python validate_data.py --datadir plida_sim_a --strict   # non-zero exit on FAIL
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import SplineTransformer

BASELINE_YEAR, TREATMENT_YEAR, OUTCOME_YEAR = 2016, 2017, 2019

# Tolerances on the estimator checks are set at roughly two standard
# deviations of the bias measured across six independent draws (see
# stability.py).  They are wide because the estimators genuinely are:
# nearest-neighbour matching has a between-draw SD of 8.4 percentage points.
# A tighter band would fail on an innocent reseed; a wider one would miss a
# design regression.
results: list[tuple[str, float, float | None, float | None, str]] = []


def check(label, value, target=None, tol=None, fmt="{:,.0f}"):
    status = "--"
    if target is not None:
        status = "PASS" if abs(value - target) <= tol else "FAIL"
    results.append((label, value, target, tol, status))
    return value


# ---------------------------------------------------------------------------
# Load and assemble, exactly as Chapter 2 will instruct
# ---------------------------------------------------------------------------

def load(datadir: Path):
    r = lambda n: pd.read_csv(datadir / f"{n}.csv")
    d = {n: r(n) for n in [
        "spine_scoping", "core_demographics", "core_locations", "census16_person",
        "pit_income", "domino_payments", "mbs_pbs_health", "epp_program",
        "reference_indices",
    ]}
    d["truth"] = pd.read_csv(datadir / "truth" / "truth_parameters.csv")
    return d


def deflate(df, idx, year_col="ref_year", cols=(), series="cpi_index"):
    out = df.merge(idx[["ref_year", series]], left_on=year_col, right_on="ref_year", how="left")
    for c in cols:
        out[c.replace("_nominal", "_real")] = out[c] / (out[series] / 100.0)
    return out


def assemble(d):
    idx = d["reference_indices"]

    pit = deflate(d["pit_income"], idx, cols=["salary_wages_nominal"])
    wide = pit.pivot_table(index="person_id", columns="ref_year",
                           values="salary_wages_real", aggfunc="first")
    wide.columns = [f"inc_{c}" for c in wide.columns]

    pay = (d["domino_payments"].groupby(["person_id", "ref_year"], as_index=False)
           .agg(fortnights=("fortnights_on_payment", "sum")))
    pay_w = pay.pivot_table(index="person_id", columns="ref_year",
                            values="fortnights", aggfunc="first")
    pay_w.columns = [f"fn_{c}" for c in pay_w.columns]

    mo = (d["domino_payments"].query("ref_year == @BASELINE_YEAR")
          .sort_values("fortnights_on_payment", ascending=False)
          .drop_duplicates("person_id").set_index("person_id")["mutual_obligation_status"])

    hl = d["mbs_pbs_health"].query("ref_year == @BASELINE_YEAR").set_index("person_id")
    loc = d["core_locations"].query("ref_year == @BASELINE_YEAR").set_index("person_id")
    # Occupation from the most recent pre-period year in which it is observed.
    # Taking 2016 alone makes its "unknown" level an exact copy of the
    # non-lodger indicator, which predicts treatment; carrying forward
    # decouples them. See Section 2.6.4.
    occ = None
    for _y in (2014, 2015, 2016):
        _s = (d["pit_income"].query("ref_year == @_y").set_index("person_id")
              ["occupation_group"].dropna())
        occ = _s if occ is None else _s.combine_first(occ)

    df = (d["core_demographics"].set_index("person_id")
          .join(d["census16_person"].set_index("person_id"), how="left")
          .join(loc[["remoteness_area", "seifa_irsd_decile", "state"]], how="left")
          .join(wide, how="left").join(pay_w, how="left")
          .join(hl[["gp_attendances", "mh_item_flag", "pbs_scripts"]], how="left")
          .join(occ.rename("occupation_group"), how="left")
          .join(mo.rename("mutual_obligation"), how="left"))
    df["mutual_obligation"] = df["mutual_obligation"].fillna("Exempt")

    prog = d["epp_program"].set_index("person_id")
    df["treated"] = df.index.isin(prog.index).astype(int)
    df["referral_type"] = prog["referral_type"].reindex(df.index).fillna("None")

    spine = d["spine_scoping"].set_index("person_id")
    df["attrited"] = (spine["last_active_year"].reindex(df.index) < OUTCOME_YEAR).astype(int)

    # structural zeros, not unknowns
    for c in ["gp_attendances", "mh_item_flag", "pbs_scripts"]:
        df[c] = df[c].fillna(0)
    for c in [c for c in df.columns if c.startswith("fn_")]:
        df[c] = df[c].fillna(0)

    return df.join(d["truth"].set_index("person_id"), rsuffix="_truth")


def design_matrix(df):
    """Covariates prepared the way a competent analyst would prepare them.

    Note what is *not* here: `referral_type`.  It is observed only for the
    treated, so it is a post-treatment variable and a perfect predictor.  The
    legitimate pre-treatment construct is `mutual_obligation`, taken from the
    DOMINO module, which is recorded for everyone.

    Missing 2016 income is imputed rather than zero-filled, with a missingness
    indicator retained: the non-lodger mechanism is MNAR, so the indicator
    carries real signal and dropping it discards the strongest confounder for
    12% of the sample.
    """
    age = BASELINE_YEAR - df["birth_year"]
    inc16 = df["inc_2016"]
    inc15 = df.get("inc_2015", pd.Series(np.nan, index=df.index))
    X = pd.DataFrame({
        "age": age,
        "female": (df["sex"] == "Female").astype(int),
        "kids": df["dependent_children"].fillna(df["dependent_children"].median()),
        "lang": (df["english_proficiency"] == "Not well").astype(int),
        "seifa": df["seifa_irsd_decile"],
        "log_inc_2015": np.log1p(inc15.fillna(inc15.median())),
        "log_inc_2016": np.log1p(inc16.fillna(inc16.median())),
        "inc_2016_missing": inc16.isna().astype(int),
        "fn_2016": df["fn_2016"],
        "lts": (df["fn_2016"] >= 20).astype(int),
        "gp": df["gp_attendances"],
        "mh": df["mh_item_flag"],
        "mo_intensive": (df["mutual_obligation"] == "Intensive").astype(int),
        "mo_full": (df["mutual_obligation"] == "Full").astype(int),
        "mo_partial": (df["mutual_obligation"] == "Partial").astype(int),
    }, index=df.index)
    edu_order = {"<Year 12": 0, "Year 12": 1, "Cert III/IV": 2, "Diploma": 3, "Bachelor+": 4}
    X["edu"] = df["highest_edu"].map(edu_order)
    X["edu"] = X["edu"].fillna(X["edu"].median())
    rem = {"Major Cities": 0, "Inner Regional": 1, "Outer Regional": 2, "Remote+": 3}
    X["remote"] = df["remoteness_area"].map(rem).fillna(0)
    X["cob_other"] = (df["country_of_birth_group"] == "Other").astype(int)
    X["cob_mesc"] = (df["country_of_birth_group"] == "MESC").astype(int)
    return X.fillna(X.median())


def smd(v, a, b):
    return (v[a].mean() - v[b].mean()) / np.sqrt((v[a].var() + v[b].var()) / 2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(datadir: Path):
    d = load(datadir)
    df = assemble(d)
    n = len(df)

    # ---- structure ----
    check("Persons", n, 50_000, 0)
    check("Person-years in core_locations", len(d["core_locations"]), 300_000, 0)
    check("Treated (%)", 100 * df["treated"].mean(), 10.74, 2.0, "{:.2f}")

    # ---- truth ----
    tau, D = df["tau_i"].values, df["treated"].values
    y = np.where(D == 1, df["y1"], df["y0"])
    true_ate, true_att = tau.mean(), tau[D == 1].mean()
    check("True ATE ($)", true_ate, 5157, 900)
    check("True ATT ($)", true_att, 6192, 1100)
    check("True ATC ($)", tau[D == 0].mean(), 5030, 900)
    check("Naive difference ($)", y[D == 1].mean() - y[D == 0].mean(), -3994, 2500)
    check("ATT exceeds ATE by (%)", 100 * (true_att / true_ate - 1), 18.4, 9.0, "{:.1f}")

    # ---- pathologies ----
    check("Census non-response (%)", 100 * (1 - len(d["census16_person"]) / n), 7.2, 2.5, "{:.2f}")
    pit16 = d["pit_income"].query("ref_year == @BASELINE_YEAR")
    check("PIT non-lodgers 2016 (%)", 100 * (1 - len(pit16) / n), 11.2, 4.0, "{:.2f}")
    check("Attrition, all (%)", 100 * df["attrited"].mean(), 12.5, 3.0, "{:.2f}")
    check("Attrition, treated (%)", 100 * df.loc[df.treated == 1, "attrited"].mean(), 17.1, 4.0, "{:.2f}")
    check("Attrition, control (%)", 100 * df.loc[df.treated == 0, "attrited"].mean(), 12.0, 3.0, "{:.2f}")
    check("Attrition differential (pp)",
          100 * (df.loc[df.treated == 1, "attrited"].mean() - df.loc[df.treated == 0, "attrited"].mean()),
          6.2, 4.0, "{:.2f}")

    idx = d["reference_indices"]
    nom16 = float(idx.loc[idx.ref_year == 2016, "cpi_index"].iloc[0])
    check("Understatement if 2016 not deflated (%)", 100 - nom16, 6.0, 1.0, "{:.2f}")

    # ---- propensity score ----
    X = design_matrix(df)
    Xs = (X - X.mean()) / X.std()
    ps = LogisticRegression(max_iter=4000, C=1e6).fit(Xs, D).predict_proba(Xs)[:, 1]
    check("Estimated PS minimum", ps.min(), 0.015, 0.030, "{:.4f}")
    check("Estimated PS maximum", ps.max(), 0.990, 0.030, "{:.4f}")
    # Overlap is better measured by the treated:control ratio in the upper
    # region than by a raw count above a single threshold: it is the ratio that
    # determines how often each control gets reused, and therefore how badly
    # the naive standard error understates (Chapter 9).
    for thr, tgt, tol in [(0.8, 7.0, 5.0), (0.9, 13.9, 12.0)]:
        nt = ((ps > thr) & (D == 1)).sum()
        nc = max(((ps > thr) & (D == 0)).sum(), 1)
        check(f"Overlap: treated:control ratio above PS {thr}", nt / nc, tgt, tol, "{:.1f}")
    check("Treated with PS > 0.80", ((ps > 0.80) & (D == 1)).sum(), 680, 450)
    check("Controls with PS > 0.80", ((ps > 0.80) & (D == 0)).sum(), 51, 45)

    for name, col in [("fortnights 2016", X["fn_2016"]), ("log income 2016", X["log_inc_2016"]),
                      ("education", X["edu"]), ("remoteness", X["remote"]),
                      ("mutual obligation = Intensive", X["mo_intensive"])]:
        check(f"Pre-match SMD: {name}", smd(col.values, D == 1, D == 0), None, None, "{:+.3f}")

    # The post-treatment trap must in fact be a trap: referral_type is observed
    # only for participants, so a model using it should separate completely.
    trap = (df["referral_type"] != "None").astype(int).values
    check("Trap: referral_type predicts D exactly (1=yes)", float((trap == D).all()), 1.0, 0.0, "{:.0f}")

    # occupation must NOT predict treatment (pure outcome predictor)
    occ = pd.get_dummies(df["occupation_group"].fillna("None")).astype(float)
    auc_occ = LogisticRegression(max_iter=2000).fit(occ, D).predict_proba(occ)[:, 1]
    check("Occupation-only PS spread (max-min)", auc_occ.max() - auc_occ.min(), 0.0, 0.12, "{:.4f}")

    # ---- estimators ----
    lo = np.log(ps / (1 - ps))
    t, c = np.where(D == 1)[0], np.where(D == 0)[0]
    nn = NearestNeighbors(n_neighbors=1).fit(lo[c].reshape(-1, 1))
    dist, ii = nn.kneighbors(lo[t].reshape(-1, 1))
    for cal in [0.2, 0.1, 0.05]:
        k = dist.ravel() <= cal * lo.std()
        mt, mc = t[k], c[ii.ravel()[k]]
        est, truth = (y[mt] - y[mc]).mean(), tau[mt].mean()
        check(f"NN matching, caliper {cal} SD: bias (%)",
              100 * (est - truth) / truth, -3.9, 20.0, "{:+.2f}")

    w = np.where(D == 1, D.mean() / ps, (1 - D.mean()) / (1 - ps))
    ipw = (np.sum(w * D * y) / np.sum(w * D)) - (np.sum(w * (1 - D) * y) / np.sum(w * (1 - D)))
    check("IPTW ATE untrimmed: bias (%)", 100 * (ipw - true_ate) / true_ate, -20.6, 25.0, "{:+.2f}")
    check("IPTW max weight", w.max(), 44.0, 60.0, "{:.1f}")

    sup = (ps > 0.05) & (ps < 0.95)
    ws = np.where(D[sup] == 1, D[sup].mean() / ps[sup], (1 - D[sup].mean()) / (1 - ps[sup]))
    ds, ys = D[sup], y[sup]
    ipw_t = (np.sum(ws * ds * ys) / np.sum(ws * ds)) - (np.sum(ws * (1 - ds) * ys) / np.sum(ws * (1 - ds)))
    check("IPTW ATE trimmed: bias (%)", 100 * (ipw_t - tau[sup].mean()) / tau[sup].mean(), -4.2, 17.0, "{:+.2f}")

    g = dict(n_estimators=250, max_depth=3, learning_rate=0.05, random_state=1)
    m1 = GradientBoostingRegressor(**g).fit(X[D == 1], y[D == 1]).predict(X)
    m0 = GradientBoostingRegressor(**g).fit(X[D == 0], y[D == 0]).predict(X)
    score = m1 - m0 + D * (y - m1) / ps - (1 - D) * (y - m0) / (1 - ps)
    # Untrimmed AIPW inherits IPTW's instability: the influence-function
    # correction has extreme tails wherever the propensity score approaches 0
    # or 1.  Informational, because the lesson is that it must be trimmed.
    check("AIPW untrimmed: bias (%)", 100 * (score.mean() - true_ate) / true_ate, None, None, "{:+.2f}")
    check("AIPW correction term SD ($)", (score - (m1 - m0)).std(), None, None)
    check("AIPW trimmed: bias (%)",
          100 * (score[sup].mean() - tau[sup].mean()) / tau[sup].mean(), -6.0, 20.0, "{:+.2f}")

    for K in [5, 20]:
        qs = np.unique(np.quantile(ps[D == 1], np.linspace(0, 1, K + 1)))
        qs[0], qs[-1] = 0, 1
        sub = pd.cut(ps, qs, labels=False, include_lowest=True)
        num = den = tnum = 0
        for s in np.unique(sub[~pd.isna(sub)]):
            m = sub == s
            if (m & (D == 1)).sum() > 5 and (m & (D == 0)).sum() > 5:
                nn_ = (m & (D == 1)).sum()
                num += nn_ * (y[m & (D == 1)].mean() - y[m & (D == 0)].mean())
                tnum += nn_ * tau[m & (D == 1)].mean()
                den += nn_
        # Coarse subclassification is genuinely poor in this dataset once an
    # unmeasured confounder is present. The band is wide because the method is.
    check(f"Subclassification, {K} strata: bias (%)", 100 * (num - tnum) / tnum, -12.0, 30.0, "{:+.2f}")

    B = SplineTransformer(n_knots=25, degree=3).fit_transform(ps.reshape(-1, 1))
    Z = np.hstack([B, Xs.values])
    f1 = Ridge(1.0).fit(Z[D == 1], y[D == 1]).predict(Z)
    f0 = Ridge(1.0).fit(Z[D == 0], y[D == 0]).predict(Z)
    check("Spline-on-PS reg-adj, trimmed: bias (%)",
          100 * ((f1 - f0)[sup].mean() - tau[sup].mean()) / tau[sup].mean(), -8.0, 20.0, "{:+.2f}")

    # ---- the attrition lesson ----
    surv = df["attrited"].values == 0
    check("True ATT among survivors ($)", tau[surv & (D == 1)].mean(), None, None)
    check("ATT shift from attrition (%)",
          100 * (tau[surv & (D == 1)].mean() - true_att) / true_att, -5.4, 4.5, "{:+.2f}")
    Xsv = Xs[surv]
    psv = LogisticRegression(max_iter=4000, C=1e6).fit(Xsv, D[surv]).predict_proba(Xsv)[:, 1]
    lov = np.log(psv / (1 - psv))
    iv = np.where(surv)[0]
    tv, cv = iv[D[surv] == 1], iv[D[surv] == 0]
    nnv = NearestNeighbors(n_neighbors=1).fit(lov[D[surv] == 0].reshape(-1, 1))
    dv, jv = nnv.kneighbors(lov[D[surv] == 1].reshape(-1, 1))
    kv = dv.ravel() <= 0.1 * lov.std()
    mtv, mcv = tv[kv], cv[jv.ravel()[kv]]
    est_cc = (y[mtv] - y[mcv]).mean()
    check("Complete-case PSM vs survivor ATT (%)",
          100 * (est_cc - tau[mtv].mean()) / tau[mtv].mean(), -3.9, 20.0, "{:+.2f}")
    check("Complete-case PSM vs full-population ATT (%)",
          100 * (est_cc - true_att) / true_att, -12.0, 20.0, "{:+.2f}")

    return results


def report(rows, strict):
    w = max(len(r[0]) for r in rows) + 2
    print(f"\n{'CHECK'.ljust(w)}{'VALUE':>14}{'TARGET':>12}{'TOL':>10}   STATUS")
    print("-" * (w + 50))
    fails = 0
    for label, value, target, tol, status in rows:
        fmt = "{:>14,.2f}" if abs(value) < 1000 else "{:>14,.0f}"
        tgt = f"{target:>12,.2f}" if target is not None and abs(target) < 1000 else (
            f"{target:>12,.0f}" if target is not None else " " * 12)
        tl = f"{tol:>10,.2f}" if tol is not None else " " * 10
        mark = {"PASS": "  ok", "FAIL": "  FAIL <<<", "--": "  (info)"}[status]
        print(f"{label.ljust(w)}{fmt.format(value)}{tgt}{tl}{mark}")
        fails += status == "FAIL"
    print("-" * (w + 50))
    print(f"{len([r for r in rows if r[4] == 'PASS'])} passed, {fails} failed, "
          f"{len([r for r in rows if r[4] == '--'])} informational\n")
    return 1 if (fails and strict) else 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--datadir", type=Path, default=Path("plida_sim_a"))
    p.add_argument("--strict", action="store_true")
    a = p.parse_args()
    raise SystemExit(report(run(a.datadir), a.strict))
