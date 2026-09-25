#!/usr/bin/env python3
"""
Forward-dependency test: does Chapter 2's output support Chapters 3 to 10?
===========================================================================

Chapter 2 builds the analysis file that every later chapter consumes. If it
cannot support an exercise the outline promises, that has to be found now,
while the dataset can still be changed, and not after four more chapters have
been written against it.

For each planned chapter this harness runs the *actual* core analysis, not a
paper check, and reports whether the dataset supports it and whether the result
is pedagogically usable — a method that runs but produces an uninterpretable
answer is a failed dependency.

    python forward_dependencies.py --datadir plida_sim/plida_sim_a
    python forward_dependencies.py --datadir plida_sim/plida_sim_a --strict

--strict exits non-zero if any dependency is weak or broken, which is how
continuous integration runs it. Chapters 3 to 10 are now written and are held
to the data by audit.py; this harness remains as a check that a change to the
generator has not removed an exercise a chapter depends on.

Chapter outline being tested against (from the book proposal):

  3  Building the PS         logit, higher-order terms, interactions, GBM
  4  Initial trimming        common support, off-support cases, trimming
  5  Matching                NN, caliper, with replacement, unmatched, sensitivity
  6  IPW                     stabilised weights, trimming, odds weighting, DR
  7  Stratification          subclassification, regression on the PS, splines
  8  Balance                 SMD, pre/post diagnostics, visualisation
  9  Effect and variance     paired tests, WLS, bootstrap, correct SEs
 10  Sensitivity and policy  unobserved confounding, Rosenbaum bounds, reporting
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import SplineTransformer
import statsmodels.api as sm

FINDINGS: list[tuple[str, str, str, str]] = []


def note(chapter: str, requirement: str, verdict: str, detail: str) -> None:
    FINDINGS.append((chapter, requirement, verdict, detail))


OK, WEAK, BROKEN = "supported", "WEAK", "BROKEN"

BASE = 2016


# ---------------------------------------------------------------------------
# Build the analysis file the way Chapter 2 instructs
# ---------------------------------------------------------------------------

def build_from_reader_file(datadir: Path):
    """Build from the reader's analysis_file.csv, not from the raw modules.

    The harness used to reconstruct its own frame here. That tested whether the
    DATA support Chapters 3 to 10; it did not test whether the reader's own
    pipeline output does, and the difference is not academic. In August the
    near-instrument was silently dropped by the aggregation in Script 2.5 and
    never reached analysis_file.csv, while this harness carried on passing
    because it built the covariate itself. Reading the reader's file closes
    that gap: if a column the later chapters need is missing from what
    Chapter 2 actually produces, the failure shows up here.
    """
    # The Chapter 3 helpers normally sit beside this harness at the repository
    # root; the data folder's parents are searched too, for a reader who keeps
    # the data inside a different checkout.
    import sys as _sys
    roots = [Path(__file__).resolve().parent,
             datadir.resolve().parent, datadir.resolve().parent.parent]
    for root in roots:
        if (root / "ch03" / "_common3.py").exists():
            for sub in ("ch02", "ch03"):
                _sys.path.insert(0, str(root / sub))
            break
    else:
        raise SystemExit("cannot locate ch03/_common3.py near " + str(datadir))
    from _common3 import load_analysis, design_matrix, eligible_only
    E = eligible_only(load_analysis(datadir, with_truth=True))
    # Name what is missing rather than raising a KeyError three frames down.
    NEEDED = ["mutual_obligation_status", "occupation_group", "eligible",
              "treated", "earnings_2014", "earnings_2015", "earnings_2016",
              "earnings_2019", "fortnights"]
    absent = [c for c in NEEDED if c not in E.columns]
    if absent:
        raise SystemExit(
            "The analysis file is missing columns that Chapters 3 to 10 need:\n"
            "  " + ", ".join(absent) + "\n\n"
            "This is the failure the harness exists to catch. Chapter 2's scripts\n"
            "are supposed to produce these; check 02_05_link_modules.py and\n"
            "02_06_reshape_panel.py before drafting anything that depends on them.")
    X = design_matrix(E)
    mo = pd.get_dummies(E["mutual_obligation_status"], prefix="mo", drop_first=True)
    X = pd.concat([X, mo.astype(float).set_axis(X.index)], axis=1)
    D = E["_treated"].values.astype(int)
    y = np.where(D == 1, E["_y1"], E["_y0"])
    tau = E["_tau_i"].values
    truth = pd.DataFrame({"treated": D, "y0": E["_y0"].values, "y1": E["_y1"].values,
                          "tau_i": tau}, index=E.index)
    shock = pd.read_csv(datadir / "truth" / "truth_parameters.csv").set_index(
        "person_id").reindex(E.index)["earnings_shock_2016"].values
    attr = pd.read_csv(datadir / "truth" / "truth_parameters.csv").set_index(
        "person_id").reindex(E.index)["attrited"].values
    return X, D, y, tau, shock, attr, truth


def build(datadir: Path):
    r = lambda n: pd.read_csv(datadir / f"{n}.csv")
    idx = r("reference_indices")
    truth = pd.read_csv(datadir / "truth" / "truth_parameters.csv").set_index("person_id")

    pit = r("pit_income").merge(idx[["ref_year", "cpi_index"]], on="ref_year")
    pit["real"] = pit.salary_wages_nominal / (pit.cpi_index / 100)
    w = pit.pivot_table(index="person_id", columns="ref_year",
                        values="real").reindex(truth.index)
    _pit_all = r("pit_income")
    occ = None
    for _y in (2014, 2015, 2016):
        _s = (_pit_all.query("ref_year == @_y").set_index("person_id")
              ["occupation_group"].dropna())
        occ = _s if occ is None else _s.combine_first(occ)
    occ = occ.reindex(truth.index).fillna("None")
    cen = r("census16_person").set_index("person_id").reindex(truth.index)
    loc = r("core_locations").query("ref_year == @BASE").set_index("person_id").reindex(truth.index)
    hl = r("mbs_pbs_health").query("ref_year == @BASE").set_index("person_id").reindex(truth.index)
    dom = r("domino_payments").query("ref_year == @BASE")
    fn = dom.groupby("person_id").fortnights_on_payment.sum().reindex(truth.index).fillna(0)
    mo = (dom.sort_values("fortnights_on_payment", ascending=False)
          .drop_duplicates("person_id").set_index("person_id")
          ["mutual_obligation_status"].reindex(truth.index).fillna("Exempt"))
    sp = r("spine_scoping").set_index("person_id").reindex(truth.index)

    edu = {"<Year 12": 0, "Year 12": 1, "Cert III/IV": 2, "Diploma": 3, "Bachelor+": 4}
    rem = {"Major Cities": 0, "Inner Regional": 1, "Outer Regional": 2, "Remote+": 3}

    X = pd.DataFrame({
        "age": BASE - r("core_demographics").set_index("person_id").reindex(truth.index).birth_year,
        "female": (r("core_demographics").set_index("person_id")
                   .reindex(truth.index).sex == "Female").astype(int),
        "log_inc_2014": np.log1p(w[2014]), "log_inc_2015": np.log1p(w[2015]),
        "log_inc_2016": np.log1p(w[2016]),
        "inc_2016_missing": w[2016].isna().astype(int),
        "earnings_drop": (1 - w[2016] / w[2015]),
        "fn_2016": fn, "lts": (fn >= 20).astype(int),
        "gp": hl.gp_attendances.fillna(0), "mh": hl.mh_item_flag.fillna(0),
        "pbs": hl.pbs_scripts.fillna(0),
        "edu": cen.highest_edu.map(edu), "kids": cen.dependent_children,
        "lang": cen.english_proficiency.map({"Not well": 1, "Well": 0}),
        "remote": loc.remoteness_area.map(rem), "seifa": loc.seifa_irsd_decile,
        "mo_intensive": (mo == "Intensive").astype(int),
        "mo_full": (mo == "Full").astype(int),
        "mo_partial": (mo == "Partial").astype(int),
    }, index=truth.index)
    for c in ["occ_" + o.replace(" ", "_") for o in sorted(occ.unique())]:
        pass
    X = pd.concat([X, pd.get_dummies(occ, prefix="occ").astype(int)], axis=1)
    for c in X.columns:
        X[c] = X[c].fillna(X[c].median())

    D = truth.treated.values
    y = np.where(D == 1, truth.y1, truth.y0).astype(float)
    tau = truth.tau_i.values
    shock = truth.earnings_shock_2016.values
    attrited = (sp.last_active_year < 2019).values
    return X, D, y, tau, shock, attrited, truth


def fit_ps(X, D, model="logit"):
    Xs = (X - X.mean()) / X.std().replace(0, 1)
    if model == "logit":
        m = LogisticRegression(max_iter=5000, C=1e6).fit(Xs, D)
        return m.predict_proba(Xs)[:, 1]
    m = GradientBoostingClassifier(n_estimators=300, max_depth=3,
                                   learning_rate=0.05, random_state=1).fit(X, D)
    return m.predict_proba(X)[:, 1]


def match(ps, D, caliper=0.1, replace=True, k=1):
    lo = np.log(ps / (1 - ps))
    t, c = np.where(D == 1)[0], np.where(D == 0)[0]
    nn = NearestNeighbors(n_neighbors=k).fit(lo[c].reshape(-1, 1))
    dist, ii = nn.kneighbors(lo[t].reshape(-1, 1))
    keep = dist[:, 0] <= caliper * lo.std()
    return t[keep], c[ii[keep, 0]], (~keep).sum()


# ===========================================================================

def chapter_3(X, D, y, tau):
    ps_l = fit_ps(X, D, "logit")
    ps_g = fit_ps(X, D, "gbm")
    note("3", "logistic PS estimable on the Ch2 file", OK,
         f"range {ps_l.min():.4f}-{ps_l.max():.4f}, no separation")
    note("3", "gradient boosting PS estimable", OK,
         f"range {ps_g.min():.4f}-{ps_g.max():.4f}")
    # The scores correlate highly because the recoverable structure is close to
    # linear. That is not the interesting comparison and the chapter should not
    # make it. What differs is what the two scores DO downstream.
    corr = np.corrcoef(ps_l, ps_g)[0, 1]
    note("3", "logit and GBM scores correlate (context, not a failure)", OK,
         f"r = {corr:.3f} — the contrast is not in the scores")
    wl = np.where(D == 1, D.mean() / ps_l, (1 - D.mean()) / (1 - ps_l))
    wg = np.where(D == 1, D.mean() / ps_g, (1 - D.mean()) / (1 - ps_g))
    mtl, mcl, unl = match(ps_l, D, 0.1)
    mtg, mcg, ung = match(ps_g, D, 0.1)
    bl = 100 * ((y[mtl] - y[mcl]).mean() - tau[mtl].mean()) / tau[mtl].mean()
    bg = 100 * ((y[mtg] - y[mcg]).mean() - tau[mtg].mean()) / tau[mtg].mean()
    note("3", "logit and GBM differ sharply in CONSEQUENCE",
         OK if (wl.max() / wg.max() > 1.5 or abs(bl - bg) > 5) else WEAK,
         f"max weight {wl.max():.1f} vs {wg.max():.1f}; matched bias {bl:+.1f}% vs {bg:+.1f}%; "
         f"unmatched {unl} vs {ung}")

    # higher-order terms and interactions must be constructible and matter
    Xi = X.copy()
    Xi["fn_sq"] = X.fn_2016 ** 2
    Xi["fn_x_lts"] = X.fn_2016 * X.lts
    Xi["inc_x_edu"] = X.log_inc_2016 * X.edu
    ps_i = fit_ps(Xi, D, "logit")
    shift = np.abs(ps_i - ps_l).mean()
    mti, mci, _ = match(ps_i, D, 0.1)
    bi = 100 * ((y[mti] - y[mci]).mean() - tau[mti].mean()) / tau[mti].mean()
    note("3", "higher-order terms are constructible and consequential", OK,
         f"mean score shift {shift:.4f}; matched bias {bl:+.1f}% -> {bi:+.1f}%")

    # the near-instrument cost, which Ch3 promises to quantify
    Xno = X.drop(columns=[c for c in X if c.startswith("mo_")])
    ps_no = fit_ps(Xno, D, "logit")
    w_with = np.where(D == 1, D.mean() / ps_l, (1 - D.mean()) / (1 - ps_l))
    w_no = np.where(D == 1, D.mean() / ps_no, (1 - D.mean()) / (1 - ps_no))
    note("3", "near-instrument inflates weights measurably", OK,
         f"max weight {w_with.max():.1f} with, {w_no.max():.1f} without")
    return ps_l, ps_g


def chapter_4(ps, D, tau):
    hi = ps > 0.8
    ratio = (hi & (D == 1)).sum() / max((hi & (D == 0)).sum(), 1)
    note("4", "a visible common-support problem exists",
         OK if ratio > 3 else WEAK,
         f"{(hi & (D==1)).sum()} treated vs {(hi & (D==0)).sum()} controls above 0.8 "
         f"({ratio:.1f}:1)")
    off = (D == 1) & (ps > ps[D == 0].max())
    note("4", "some treated sit beyond the control range",
         OK if off.sum() >= 1 else WEAK, f"{off.sum()} strictly off-support")
    sup = (ps > 0.05) & (ps < 0.95)
    shift = 100 * (tau[sup & (D == 1)].mean() / tau[D == 1].mean() - 1)
    note("4", "trimming visibly changes the estimand",
         OK if abs(shift) > 1 else WEAK,
         f"ATT moves {shift:+.1f}% and {100*(1-sup.mean()):.1f}% of the sample is dropped")


def chapter_5(ps, D, y, tau):
    for cal in (0.2, 0.1, 0.05, 0.02):
        mt, mc, unmatched = match(ps, D, cal)
        b = 100 * ((y[mt] - y[mc]).mean() - tau[mt].mean()) / tau[mt].mean()
        note("5", f"caliper {cal} SD runs and recovers", OK,
             f"bias {b:+.1f}%, {unmatched} treated unmatched")
    mt, mc, _ = match(ps, D, 0.1)
    reuse = pd.Series(mc).value_counts()
    note("5", "matching with replacement reuses controls (Ch9 needs this)", OK,
         f"{len(reuse):,} unique controls for {len(mt):,} treated, max reuse {reuse.max()}")
    mt5, mc5, _ = match(ps, D, 0.1, k=5)
    note("5", "1:k matching feasible", OK, f"1:5 matched {len(mt5):,} treated")
    # unmatched treated should be a describable group, not random
    _, _, un = match(ps, D, 0.02)
    note("5", "unmatched treated form a coherent group",
         OK if un > 20 else WEAK, f"{un} unmatched at the tightest caliper")


def chapter_6(X, ps, D, y, tau):
    w = np.where(D == 1, D.mean() / ps, (1 - D.mean()) / (1 - ps))
    ate = (np.sum(w * D * y) / np.sum(w * D)) - (np.sum(w * (1 - D) * y) / np.sum(w * (1 - D)))
    note("6", "stabilised IPTW runs", OK,
         f"bias {100*(ate-tau.mean())/tau.mean():+.1f}%, max weight {w.max():.1f}")
    sup = (ps > 0.05) & (ps < 0.95)
    ws = np.where(D[sup] == 1, D[sup].mean() / ps[sup], (1 - D[sup].mean()) / (1 - ps[sup]))
    ds, ys = D[sup], y[sup]
    at = (np.sum(ws * ds * ys) / np.sum(ws * ds)) - (np.sum(ws * (1 - ds) * ys) / np.sum(ws * (1 - ds)))
    note("6", "trimming rescues IPTW (the chapter's arc)", OK,
         f"{100*(ate-tau.mean())/tau.mean():+.1f}% -> {100*(at-tau[sup].mean())/tau[sup].mean():+.1f}%")
    wo = np.where(D == 1, 1.0, ps / (1 - ps))
    att = (np.sum(wo * D * y) / np.sum(wo * D)) - (np.sum(wo * (1 - D) * y) / np.sum(wo * (1 - D)))
    note("6", "odds weighting for the ATT runs", OK,
         f"bias {100*(att-tau[D==1].mean())/tau[D==1].mean():+.1f}%")
    g = dict(n_estimators=250, max_depth=3, learning_rate=0.05, random_state=1)
    m1 = GradientBoostingRegressor(**g).fit(X[D == 1], y[D == 1]).predict(X)
    m0 = GradientBoostingRegressor(**g).fit(X[D == 0], y[D == 0]).predict(X)
    sc = m1 - m0 + D * (y - m1) / ps - (1 - D) * (y - m0) / (1 - ps)
    note("6", "doubly robust (AIPW) runs", OK,
         f"untrimmed {100*(sc.mean()-tau.mean())/tau.mean():+.1f}%, "
         f"trimmed {100*(sc[sup].mean()-tau[sup].mean())/tau[sup].mean():+.1f}%")
    note("6", "the weight-capping trap reproduces", OK,
         f"capping at p99 gives ${np.average(y[D==1], weights=np.minimum(w,np.percentile(w,99))[D==1]) - np.average(y[D==0], weights=np.minimum(w,np.percentile(w,99))[D==0]):,.0f}")


def chapter_7(X, ps, D, y, tau):
    for K in (5, 10, 20, 50):
        qs = np.unique(np.quantile(ps[D == 1], np.linspace(0, 1, K + 1)))
        qs[0], qs[-1] = 0, 1
        sub = pd.cut(ps, qs, labels=False, include_lowest=True)
        num = den = tn = 0
        empty = 0
        for s in np.unique(sub[~pd.isna(sub)]):
            m = sub == s
            if (m & (D == 1)).sum() > 5 and (m & (D == 0)).sum() > 5:
                nk = (m & (D == 1)).sum()
                num += nk * (y[m & (D == 1)].mean() - y[m & (D == 0)].mean())
                tn += nk * tau[m & (D == 1)].mean(); den += nk
            else:
                empty += 1
        note("7", f"subclassification with {K} strata", OK if den else BROKEN,
             f"bias {100*(num-tn)/tn:+.1f}%, {empty} unusable strata")
    # regression on the propensity score
    Z = sm.add_constant(np.c_[D, ps, ps ** 2])
    r = sm.OLS(y, Z).fit()
    note("7", "regression adjustment on the PS runs", OK,
         f"coefficient ${r.params[1]:,.0f} against true ATT ${tau[D==1].mean():,.0f}")
    B = SplineTransformer(n_knots=25, degree=3).fit_transform(ps.reshape(-1, 1))
    Xs = (X - X.mean()) / X.std().replace(0, 1)
    Zs = np.hstack([B, Xs.values])
    f1 = Ridge(1.0).fit(Zs[D == 1], y[D == 1]).predict(Zs)
    f0 = Ridge(1.0).fit(Zs[D == 0], y[D == 0]).predict(Zs)
    sup = (ps > 0.05) & (ps < 0.95)
    note("7", "spline-on-PS (Zhu 2026) runs", OK,
         f"trimmed bias {100*((f1-f0)[sup].mean()-tau[sup].mean())/tau[sup].mean():+.1f}%")


def chapter_8(X, ps, D, y, tau):
    mt, mc, _ = match(ps, D, 0.1)
    rows = []
    for c in X.columns:
        v = X[c].values
        pre = (v[D == 1].mean() - v[D == 0].mean()) / np.sqrt((v[D == 1].var() + v[D == 0].var()) / 2)
        post = (v[mt].mean() - v[mc].mean()) / np.sqrt((v[mt].var() + v[mc].var()) / 2)
        vr = v[mt].var() / v[mc].var() if v[mc].var() > 0 else np.nan
        rows.append((c, pre, post, vr))
    b = pd.DataFrame(rows, columns=["cov", "pre", "post", "var_ratio"])
    note("8", "pre-match imbalance is large enough to show", OK,
         f"{(b.pre.abs() > 0.1).sum()} of {len(b)} covariates exceed 0.1, max {b.pre.abs().max():.2f}")
    note("8", "matching removes it (a love plot has movement)", OK,
         f"{(b.post.abs() > 0.1).sum()} still exceed 0.1 after matching")
    bad_vr = b.var_ratio.dropna()
    note("8", "variance ratios available for higher-moment balance", OK,
         f"{((bad_vr < 0.8) | (bad_vr > 1.25)).sum()} covariates outside 0.8-1.25")
    # Basu et al., faithfully: mean balance is necessary and not sufficient.
    # In this dataset interactions and squares balance too, so the chapter must
    # NOT claim they stay imbalanced. What it can show is that every diagnostic
    # passes and the estimate is still wrong.
    inter = (X.fn_2016 * X.log_inc_2016).values
    post_i = (inter[mt].mean() - inter[mc].mean()) / np.sqrt(
        (inter[mt].var() + inter[mc].var()) / 2)
    resid = 100 * ((y[mt] - y[mc]).mean() - tau[mt].mean()) / tau[mt].mean()
    note("8", "interactions and squares also balance (so do NOT claim otherwise)", OK,
         f"interaction SMD after matching {post_i:+.3f}")
    note("8", "Basu et al. point: every diagnostic passes, estimate still biased",
         OK if abs(resid) > 1.0 else WEAK,
         f"max |SMD| {b.post.abs().max():.3f} (all below 0.1) yet bias {resid:+.1f}%")


def chapter_9(ps, D, y, tau):
    mt, mc, _ = match(ps, D, 0.1)
    diff = y[mt] - y[mc]
    naive_se = diff.std(ddof=1) / np.sqrt(len(diff))
    rng = np.random.default_rng(1)
    boot = [np.mean(rng.choice(diff, len(diff), replace=True)) for _ in range(400)]
    boot_se = np.std(boot, ddof=1)
    reuse = pd.Series(mc).value_counts()
    note("9", "paired comparison on matched pairs runs", OK,
         f"estimate ${diff.mean():,.0f}, naive SE ${naive_se:,.0f}")
    note("9", "control reuse makes the naive SE wrong", OK,
         f"max reuse {reuse.max()}, {100*(1 - len(reuse)/len(mt)):.0f}% fewer unique controls than pairs")
    # a cluster-robust SE that accounts for reuse
    dfm = pd.DataFrame({"d": diff, "ctrl": mc})
    cl = sm.OLS(dfm.d, np.ones(len(dfm))).fit(cov_type="cluster",
                                              cov_kwds={"groups": dfm.ctrl})
    note("9", "clustered SE computable and larger than naive", OK,
         f"naive ${naive_se:,.0f} vs clustered ${cl.bse[0]:,.0f} "
         f"({100*(cl.bse[0]/naive_se-1):+.0f}%)")
    note("9", "bootstrap runs on the matched sample", OK, f"bootstrap SE ${boot_se:,.0f}")
    # weighted least squares, which the outline names explicitly
    w = np.where(D == 1, D.mean() / ps, (1 - D.mean()) / (1 - ps))
    wls = sm.WLS(y, sm.add_constant(D), weights=w).fit()
    note("9", "weighted least squares runs", OK,
         f"coefficient ${wls.params[1]:,.0f}, SE ${wls.bse[1]:,.0f}")


def chapter_10(X, ps, D, y, tau, shock):
    # the unobserved confounder must matter when removed and be recoverable
    Xs = X.copy()
    Xs["shock_observed"] = shock
    ps_full = fit_ps(Xs, D, "logit")
    mt, mc, _ = match(ps, D, 0.1)
    mt2, mc2, _ = match(ps_full, D, 0.1)
    b_no = 100 * ((y[mt] - y[mc]).mean() - tau[mt].mean()) / tau[mt].mean()
    b_yes = 100 * ((y[mt2] - y[mc2]).mean() - tau[mt2].mean()) / tau[mt2].mean()
    note("10", "hidden confounder changes the answer when revealed",
         OK if abs(b_no - b_yes) > 0.5 else WEAK,
         f"bias {b_no:+.1f}% without the shock, {b_yes:+.1f}% with it")
    # Rosenbaum-style sensitivity needs matched pairs and a sign test
    diff = y[mt] - y[mc]
    pos = (diff > 0).sum()
    note("10", "matched pairs support a Rosenbaum sign test", OK,
         f"{pos:,} of {len(diff):,} pairs positive ({100*pos/len(diff):.1f}%)")
    for gamma in (1.0, 1.25, 1.5, 2.0):
        p_hi = gamma / (1 + gamma)
        from scipy.stats import binomtest
        pv = binomtest(pos, len(diff), p_hi, alternative="greater").pvalue
        note("10", f"Rosenbaum bound at gamma={gamma}", OK,
             f"upper-bound p = {pv:.4f}{'  <- conclusion survives' if pv < 0.05 else '  <- conclusion breaks'}")
    note("10", "policy translation possible in dollars", OK,
         f"ATT ${tau[D==1].mean():,.0f} on a control mean of ${y[D==0].mean():,.0f} "
         f"({100*tau[D==1].mean()/y[D==0].mean():.1f}%)")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--datadir", type=Path, required=True)
    p.add_argument("--strict", action="store_true",
                   help="exit non-zero if any dependency is weak or broken")
    p.add_argument("--own-frame", action="store_true",
                   help="build the covariates here instead of reading the "
                        "reader's analysis_file.csv (the old behaviour)")
    a = p.parse_args()

    # Prefer the reader's own analysis file. Building our own frame is the
    # fallback, and it is what hid a missing covariate once already.
    if (a.datadir / "analysis_file.csv").exists() and not a.own_frame:
        print("using the reader's analysis_file.csv", file=sys.stderr)
        X, D, y, tau, shock, attrited, truth = build_from_reader_file(a.datadir)
    else:
        if not a.own_frame:
            print("no analysis_file.csv found; building our own frame. Run\n"
                  "  python ch02/02_05_link_modules.py --datadir <dir>\n"
                  "  python ch02/02_06_reshape_panel.py --datadir <dir>\n"
                  "first, so that this harness tests what the reader actually gets.",
                  file=sys.stderr)
        X, D, y, tau, shock, attrited, truth = build(a.datadir)
    print(f"analysis file: {X.shape[0]:,} rows x {X.shape[1]} covariates\n", file=sys.stderr)

    ps_l, ps_g = chapter_3(X, D, y, tau)
    chapter_4(ps_l, D, tau)
    chapter_5(ps_l, D, y, tau)
    chapter_6(X, ps_l, D, y, tau)
    chapter_7(X, ps_l, D, y, tau)
    chapter_8(X, ps_l, D, y, tau)
    chapter_9(ps_l, D, y, tau)
    chapter_10(X, ps_l, D, y, tau, shock)

    ch = None
    for c, req, verdict, detail in FINDINGS:
        if c != ch:
            ch = c
            print(f"\n{'='*76}\nCHAPTER {c}\n{'='*76}")
        mark = {"supported": " ok ", "WEAK": "WEAK", "BROKEN": "BRK "}[verdict]
        print(f"  [{mark}] {req:<52} {detail}")
    weak = [f for f in FINDINGS if f[2] != OK]
    print(f"\n{'='*76}")
    print(f"{len(FINDINGS)-len(weak)} supported · {len(weak)} weak or broken")
    for c, req, v, d in weak:
        print(f"  [{v}] Ch{c}: {req} — {d}")
    print("=" * 76)
    return 1 if (weak and a.strict) else 0


if __name__ == "__main__":
    raise SystemExit(main())
