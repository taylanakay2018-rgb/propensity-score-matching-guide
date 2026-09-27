#!/usr/bin/env python3
"""
Script 10.1 — Where the remaining bias comes from, across forty draws
=====================================================================
Chapter 10, Sections 10.2 and 10.4.2 to 10.4.3. Produces Tables 10.1 and 10.4
and the figures quoted in Sections 10.2.1 and 10.4.3.

Chapter 3's propensity model is refitted with terms added in turn: first
observed ones it did not use, then, from the generator's truth file, the
pre-programme earnings shock and the employability score that no real
analysis could include. Each score feeds odds weighting, the doubly robust
estimator (whose outcome model gains the same terms) and Mahalanobis
matching, scored against the truth. The truth file is read for scoring and for
the two unobservable terms; nothing else here uses it.

It generates its own draws and ignores --datadir.

    python ch10/10_01_sources_of_bias.py
    python ch10/10_01_sources_of_bias.py --quick
"""
import sys, tempfile
import atexit, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _common10 import (cli, banner, score, make_draw, truth_file, added_terms, SPECS, fit_logit,
                       likelihood_ratio, att_weights, att_odds, outcome_design, outcome_fits,
                       att_dr, mahalanobis_match, pct, FIRST_SEED, N_DRAWS)
import numpy as np, pandas as pd

GROUPS = [("Low education (Year 12 or less)", "Higher education"),
          ("Long-term recipient", "Not a long-term recipient"),
          ("Earnings dip in 2016", "No earnings dip")]


def one_draw(seed, tmp):
    out = make_draw(seed, tmp)
    sc = score(out, "logit", with_truth=True)
    T = truth_file(out).reindex(sc["E"].index)
    shutil.rmtree(out, ignore_errors=True)
    E, X, D, ps0, y, tau = sc["E"], sc["X"], sc["D"], sc["ps"], sc["y"], sc["tau"]
    Q = outcome_design(E, X, with_occupation=True)
    ex = added_terms(E, X, T)
    mo = [c for c in ex.columns if c.startswith("mo_")]
    att = tau[D == 1].mean()
    rows, keep = [], {}
    for name, cols in list(SPECS.items()) + [("The true propensity score", None)]:
        if cols is None:
            ps, Qe = T["true_propensity"].values, Q
        elif not cols:
            ps, Qe = ps0, Q
        else:
            cols = [c for c in cols if c != "MO"] + (mo if "MO" in cols else [])
            ps = fit_logit(pd.concat([X, ex[cols]], axis=1), D)[0]
            Qe = pd.concat([Q, ex[[c for c in cols if not c.startswith("mo_")]]], axis=1)
        keep[name] = ps
        _, m0 = outcome_fits(Qe, D, y)
        ht, hc = mahalanobis_match(X, D, ps, 0.1)
        rows.append(dict(seed=seed, kind="spec", name=name,
                         odds=pct(att_odds(D, y, att_weights(ps, D)), att),
                         dr=pct(att_dr(ps, D, y, m0)[0], att),
                         maha=pct((y[ht] - y[hc]).mean(), tau[ht].mean())))
    lr, p = likelihood_ratio(X, D, ex[["earnings_2016_dollars"]])
    rows.append(dict(seed=seed, kind="lr", name="earnings in dollars", odds=lr, dr=p))
    # Section 10.4.2: subgroups, odds weighting on Chapter 3's score, then on the score with the
    # observed terms added, then with employability as well
    wo = att_weights(ps0, D)
    wb = att_weights(keep["+ education as categories and English proficiency"], D)
    wu = att_weights(keep["+ employability (truth file)"], D)
    masks = {"Low education (Year 12 or less)": X["edu"].values <= 1,
             "Long-term recipient": X["lts"].values == 1,
             "Earnings dip in 2016": X["drop_2016"].values > 0.25}
    for a_, b_ in GROUPS:
        for g, m in ((a_, masks[a_]), (b_, ~masks[a_])):
            rows.append(dict(seed=seed, kind="group", name=g, odds=att_odds(D[m], y[m], wo[m]),
                             dr=tau[m & (D == 1)].mean(), maha=int((m & (D == 1)).sum()),
                             obs=att_odds(D[m], y[m], wb[m]), emp=att_odds(D[m], y[m], wu[m])))
    # Section 10.4.3: the earlier years, complete cases
    for yr in (2017, 2018):
        yy = E[f"earnings_{yr}"].values
        ok = ~np.isnan(yy)
        rows.append(dict(seed=seed, kind="year", name=str(yr), odds=att_odds(D[ok], yy[ok], wo[ok]),
                         dr=0.55 * att if yr == 2018 else np.nan, maha=float(ok.mean())))
    rows.append(dict(seed=seed, kind="year", name="2019", odds=att_odds(D, y, wo), dr=att, maha=1.0))
    return rows


def main():
    a = cli(__doc__)
    n = 1 if a.quick else N_DRAWS
    tmp = Path(tempfile.mkdtemp())
    atexit.register(shutil.rmtree, tmp, ignore_errors=True)   # leave no draws behind
    rows = []
    for s in range(FIRST_SEED, FIRST_SEED + n):
        rows += one_draw(s, tmp)
        print(f"  draw {s} done", file=sys.stderr, flush=True)
    t = pd.DataFrame(rows)
    a.outdir.mkdir(parents=True, exist_ok=True)
    t.to_csv(a.outdir / "sources_of_bias.csv", index=False)
    report(t)


def report(t):
    nd = t.seed.nunique()
    sp = t[t.kind == "spec"]
    names = list(SPECS) + ["The true propensity score"]
    w = sp.pivot(index="seed", columns="name", values="odds")
    banner(f"Table 10.1 - where the remaining bias comes from, {nd} draw(s)")
    print(f"  {'':52s} {'Odds':>8s} {'Doubly':>8s} {'Mahal-':>8s} {'Change, odds':>16s}")
    print(f"  {'':52s} {'weighting':>8s} {'robust':>8s} {'anobis':>8s} {'(se)':>16s}")
    base = "Chapter 3's score"
    prev = {"+ 2016 earnings in dollars and age squared": base,
            "+ education as categories and English proficiency": "+ 2016 earnings in dollars and age squared",
            "+ the pre-programme earnings shock (truth file)": "+ education as categories and English proficiency",
            "+ employability (truth file)": "+ education as categories and English proficiency",
            "Employability alone (truth file)": base,
            "+ mutual obligation status": "+ education as categories and English proficiency",
            "The true propensity score": base}
    for k in names:
        q = sp[sp.name == k]
        ch = ""
        if k in prev and nd > 1:
            d = w[k] - w[prev[k]]
            ch = f"{d.mean():+.1f} ({d.std() / np.sqrt(nd):.2f})"
        print(f"  {k:52s} {q.odds.mean():+7.1f}% {q.dr.mean():+7.1f}% {q.maha.mean():+7.1f}% {ch:>16s}")
    if nd > 1:
        print(f"  standard deviation across draws, odds weighting: "
              + ", ".join(f"{k.split(' (')[0][:30]} {w[k].std():.1f}" for k in (base, "+ education as categories and English proficiency", "+ mutual obligation status",
                                                                              "The true propensity score")))
        dr = sp.pivot(index="seed", columns="name", values="dr")
        print(f"  doubly robust with mutual obligation status: {dr['+ mutual obligation status'].mean():+.1f}% "
              f"(sd {dr['+ mutual obligation status'].std():.1f}) against "
              f"{dr['+ education as categories and English proficiency'].mean():+.1f}% "
              f"(sd {dr['+ education as categories and English proficiency'].std():.1f})")
    lr = t[t.kind == "lr"].sort_values("seed")
    six = lr.head(6)
    print(f"\n  likelihood-ratio test of earnings in dollars: rejects at 5 per cent in "
          f"{int((six.dr < 0.05).sum())} of the first {len(six)} draws and {int((lr.dr < 0.05).sum())} "
          f"of {len(lr)}; median statistic {lr.odds.median():.1f}")

    banner(f"Table 10.5 - who the programme helps, {nd} draw(s)")
    g = t[t.kind == "group"].copy()
    for c in ("odds", "obs", "emp"):
        g["bias_" + c] = 100 * (g[c] - g.dr) / g.dr
    print(f"  {'':34s} {'Treated':>8s} {'Estimate':>9s} {'Truth':>8s} {'Bias':>7s} {'Observed':>9s} {'+ employ-':>9s}")
    print(f"  {'':34s} {'':>8s} {'':>9s} {'':>8s} {'':>7s} {'added':>9s} {'ability':>9s}")
    for a_, b_ in GROUPS:
        for k in (a_, b_):
            q = g[g.name == k]
            print(f"  {k:34s} {q.maha.mean():8,.0f} {q.odds.mean():9,.0f} {q.dr.mean():8,.0f} "
                  f"{q.bias_odds.mean():+6.1f}% {q.bias_obs.mean():+8.1f}% {q.bias_emp.mean():+8.1f}%")

    banner(f"Section 10.4.3 - earnings in 2017, 2018 and 2019, complete cases, {nd} draw(s)")
    y_ = t[t.kind == "year"]
    for k in ("2017", "2018", "2019"):
        q = y_[y_.name == k]
        tr = "" if q.dr.isna().all() else f"; implied truth {q.dr.mean():+,.0f}"
        print(f"  {k}: odds-weighted estimate {q.odds.mean():+,.0f}{tr}; share of persons observed "
              f"{100 * q.maha.mean():.0f}%")


if __name__ == "__main__":
    main()
