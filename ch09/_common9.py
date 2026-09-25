"""Shared helpers for the Chapter 9 scripts.

The estimators are those of Chapters 5 to 7, recomputed with those chapters'
own functions. What is new here is the standard errors: the naive ones the
earlier chapters quoted, and the ones this chapter recommends, each written
out in a few lines so that a reader can see what it accounts for.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "ch07"))
sys.path.insert(0, str(HERE.parent / "ch05"))
sys.path.insert(0, str(HERE.parent / "ch03"))
from _common7 import (cli, banner, score, nn_match, mahalanobis_match,       # noqa: E402,F401
                      att_weights, ate_weights, att_odds, ate_normalised, outcome_design,
                      outcome_fits, att_dr, make_draw, subclass, REPO, pct)
from _common6 import ate_se, att_se, ate_dr                                 # noqa: E402
from _common5 import MAHA_COLS, linear_predictor                            # noqa: E402

# The committed results of the full run: 200 draws, bootstraps on the first 40.
COMMITTED = REPO / "results" / "ch09_standard_errors_200.csv"
FIRST_SEED = 20260808
B_FULL = 100            # bootstrap replicates per draw in the multi-draw run
B_SETS = 500            # matched-set bootstrap replicates

LABELS = {"odds": "Odds weighting", "ipw_ate": "Normalised IPW (ATE)",
          "dr_att": "Doubly robust", "dr_ate": "Doubly robust (ATE)",
          "sub20": "Subclassification, 20 strata",
          "sub20_reg": "20 strata, regression within strata",
          "match": "PS matching, 1:1", "match_repl": "PS matching, with replacement",
          "maha": "Mahalanobis matching, 1:1", "maha13": "Mahalanobis matching, 1:3"}


# ---------------------------------------------------------------- estimators

def mahalanobis_sets(X, D, ps, ratio=3, caliper=0.1, cols=MAHA_COLS):
    """Section 5.6's Mahalanobis matching with `ratio` controls per treated person.

    The recommendation of Section 5.16.3, which Chapter 5 did not measure as a
    whole. Returns a list of (treated index, array of control indices).
    """
    Z = ((X[cols] - X[cols].mean()) / X[cols].std()).values
    lp = linear_predictor(ps)
    cal = caliper * lp.std()
    t, c = np.where(D == 1)[0], np.where(D == 0)[0]
    S = np.linalg.pinv(np.cov(Z[c].T))
    taken = np.zeros(len(c), bool)
    sets = []
    for ti in t[np.argsort(-ps[t])]:
        ok = (np.abs(lp[c] - lp[ti]) <= cal) & (~taken)
        if ok.sum() < ratio:
            continue
        idx = np.where(ok)[0]
        dv = Z[c[idx]] - Z[ti]
        j = idx[np.argsort(np.einsum("ij,jk,ik->i", dv, S, dv))[:ratio]]
        sets.append((ti, c[j]))
        taken[j] = True
    return sets


def estimates(X, D, y, Q, ps, full=True):
    """Every ATT (and two ATE) estimate of Chapters 5 to 7 on one sample."""
    Qv = Q.values.astype(float)
    m1, m0 = outcome_fits(Q, D, y)
    mt, mc = nn_match(ps, D, 0.1, False, 1)
    rt, rc = nn_match(ps, D, 0.1, True, 1)
    e = {"odds": att_odds(D, y, att_weights(ps, D)),
         "ipw_ate": ate_normalised(D, y, ate_weights(ps, D)),
         "dr_att": att_dr(ps, D, y, m0)[0],
         "dr_ate": ate_dr(ps, D, y, m1, m0)[0],
         "sub20": subclass(ps, D, y, 20, "ATT")[0],
         "sub20_reg": subclass(ps, D, y, 20, "ATT", Q=Qv)[0],
         "match": float((y[mt] - y[mc]).mean()),
         "match_repl": float((y[rt] - y[rc]).mean())}
    extra = {"match": (mt, mc), "match_repl": (rt, rc), "m1": m1, "m0": m0}
    if full:
        ht, hc = mahalanobis_match(X, D, ps, 0.1)
        e["maha"] = float((y[ht] - y[hc]).mean())
        sets = mahalanobis_sets(X, D, ps, 3)
        e["maha13"] = float(np.mean([y[a] - y[b].mean() for a, b in sets]))
        extra.update(maha=(ht, hc), maha13=sets)
    return e, extra


# ------------------------------------------------------------ standard errors

def expit(z):
    return 1 / (1 + np.exp(-z))


def logit_design(X, D):
    """The Chapter 3 logistic model: design with intercept, and coefficients."""
    from sklearn.linear_model import LogisticRegression
    Z = ((X - X.mean()) / X.std().replace(0, 1)).values
    m = LogisticRegression(max_iter=5000, C=1e6).fit(Z, D)
    return np.c_[np.ones(len(D)), Z], np.r_[m.intercept_, m.coef_.ravel()]


def sandwich_se(Zi, beta, D, y, estimand="ATT"):
    """Standard error with the propensity model stacked in. Fragment 9.1.

    The estimate and the logistic regression are solved together as one set of
    estimating equations, so that the uncertainty in the score is carried into
    the standard error of the estimate.
    """
    n, p = len(D), len(beta)

    def psi(th):
        b, m1, m0 = th[:p], th[p], th[p + 1]
        e = expit(Zi @ b)
        score_eq = Zi * (D - e)[:, None]                    # the logistic regression
        if estimand == "ATT":
            a, c = D * (y - m1), (1 - D) * e / (1 - e) * (y - m0)
        else:
            a, c = D / e * (y - m1), (1 - D) / (1 - e) * (y - m0)
        return np.c_[score_eq, a, c]

    e = expit(Zi @ beta)
    w1 = np.ones(n) if estimand == "ATT" else 1 / e
    w0 = e / (1 - e) if estimand == "ATT" else 1 / (1 - e)
    theta = np.r_[beta, np.average(y[D == 1], weights=w1[D == 1]),
                  np.average(y[D == 0], weights=w0[D == 0])]
    P = psi(theta)
    A = np.zeros((p + 2, p + 2))
    for k in range(p + 2):                                   # derivative, numerically
        h = 1e-5 * max(1.0, abs(theta[k]))
        up, dn = theta.copy(), theta.copy()
        up[k] += h; dn[k] -= h
        A[:, k] = (psi(up).mean(0) - psi(dn).mean(0)) / (2 * h)
    Ai = np.linalg.inv(A)
    V = Ai @ (P.T @ P / n) @ Ai.T / n
    c = np.zeros(p + 2); c[p], c[p + 1] = 1, -1
    return float(np.sqrt(c @ V @ c))


def wls_ses(D, y, w):
    """Weighted regression of y on D: default, frequency-weight and robust SEs."""
    X = np.c_[np.ones(len(D)), D]
    XtW = X.T * w
    Mi = np.linalg.inv(XtW @ X)
    e = y - X @ (Mi @ XtW @ y)
    default = np.sqrt(np.sum(w * e ** 2) / (len(y) - 2) * Mi[1, 1])      # statsmodels WLS
    freq = np.sqrt(np.sum(w * e ** 2) / (w.sum() - 2) * Mi[1, 1])       # weights as counts
    robust = np.sqrt((Mi @ ((X.T * (w * e) ** 2) @ X) @ Mi)[1, 1])      # HC0
    return float(default), float(freq), float(robust)


def paired_se(d):
    return float(d.std(ddof=1) / np.sqrt(len(d)))


def abadie_imbens_se(lp, D, y, mt, mc):
    """Abadie and Imbens's standard error for one-to-one matching with replacement.

    The reuse term adds, for each control used K times, K(K - 1) times its
    conditional variance, estimated from its nearest other control.
    """
    from sklearn.neighbors import NearestNeighbors
    d = y[mt] - y[mc]
    K = np.bincount(mc, minlength=len(D)).astype(float)
    c, used = np.where(D == 0)[0], np.where(K > 0)[0]
    _, idx = NearestNeighbors(n_neighbors=2).fit(lp[c].reshape(-1, 1)).kneighbors(
        lp[used].reshape(-1, 1))
    s2 = 0.5 * (y[used] - y[c[idx[:, 1]]]) ** 2
    v = (np.sum((d - d.mean()) ** 2) + np.sum(K[used] * (K[used] - 1) * s2)) / len(mt) ** 2
    return float(np.sqrt(v))


def bootstrap(X, D, y, Q, B, rng, full=False):
    """Resample persons, refit the score, repeat every estimator. Fragment 9.2."""
    from _common3 import fit_propensity
    n, reps = len(D), []
    for _ in range(B):
        i = rng.integers(0, n, n)
        Xb, Qb = X.iloc[i].reset_index(drop=True), Q.iloc[i].reset_index(drop=True)
        psb = fit_propensity(Xb, D[i], "logit", seed=20260808)
        reps.append(estimates(Xb, D[i], y[i], Qb, psb, full=full)[0])
    return pd.DataFrame(reps)


def all_standard_errors(X, D, y, Q, ps, tau, seed, B=0, full_boot=False):
    """Every estimate, its truth, and every candidate standard error."""
    est, ex = estimates(X, D, y, Q, ps)
    Zi, beta = logit_design(X, D)
    lp = np.log(ps / (1 - ps))
    att, ate = tau[D == 1].mean(), tau.mean()
    rows = {k: dict(estimator=k, est=v) for k, v in est.items()}

    def put(k, truth, **se):
        rows[k].update(truth=truth, **se)

    wo = att_weights(ps, D)
    d_, f_, r_ = wls_ses(D, y, wo)
    put("odds", att, se_naive=att_se(ps, D, y), se_sandwich=sandwich_se(Zi, beta, D, y, "ATT"),
        se_wls_default=d_, se_wls_freq=f_, se_wls_robust=r_)
    d_, f_, r_ = wls_ses(D, y, ate_weights(ps, D))
    put("ipw_ate", ate, se_naive=ate_se(ps, D, y), se_sandwich=sandwich_se(Zi, beta, D, y, "ATE"),
        se_wls_default=d_, se_wls_freq=f_, se_wls_robust=r_)
    put("dr_att", att, se_naive=att_dr(ps, D, y, ex["m0"])[1])
    put("dr_ate", ate, se_naive=ate_dr(ps, D, y, ex["m1"], ex["m0"])[1])
    put("sub20", att, se_naive=subclass(ps, D, y, 20, "ATT")[1])
    put("sub20_reg", att)
    mt, mc = ex["match"]
    put("match", tau[mt].mean(), se_paired=paired_se(y[mt] - y[mc]),
        se_unpaired=float(np.sqrt(y[mt].var(ddof=1) / len(mt) + y[mc].var(ddof=1) / len(mc))),
        pairs=len(mt))
    rt, rc = ex["match_repl"]
    K = np.bincount(rc, minlength=len(D)).astype(float)
    w = K.copy(); w[rt] += 1
    sel = w > 0
    d_, f_, r_ = wls_ses(D[sel], y[sel], w[sel])
    put("match_repl", tau[rt].mean(), se_paired=paired_se(y[rt] - y[rc]),
        se_ai=abadie_imbens_se(lp, D, y, rt, rc), se_wls_default=d_, se_wls_freq=f_,
        se_wls_robust=r_, pairs=len(rt), distinct=int((K > 0).sum()), max_reuse=int(K.max()))
    ht, hc = ex["maha"]
    put("maha", tau[ht].mean(), se_paired=paired_se(y[ht] - y[hc]), pairs=len(ht))
    sets = ex["maha13"]
    t13 = np.array([a for a, _ in sets])
    d13 = np.array([y[a] - y[b].mean() for a, b in sets])
    put("maha13", tau[t13].mean(), se_paired=paired_se(d13), pairs=len(t13))

    rng = np.random.default_rng(seed)
    for k, d in (("match", y[mt] - y[mc]), ("match_repl", y[rt] - y[rc]),
                 ("maha", y[ht] - y[hc]), ("maha13", d13)):
        bs = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(B_SETS)]
        rows[k]["se_boot_sets"] = float(np.std(bs, ddof=1))
    reps = None
    if B:
        reps = bootstrap(X, D, y, Q, B, rng, full=full_boot)
        for k in reps.columns:
            rows[k]["se_boot"] = float(reps[k].std(ddof=1))
    out = pd.DataFrame(rows.values())
    out.insert(0, "seed", seed)
    return out, reps
