#!/usr/bin/env python3
"""
PLIDA-SIM generator
===================

Builds the synthetic dataset for *The Applied Researcher's Guide to Propensity Score Matching:
Python Scripts for Data Preparation and Robust Causal Effects* (Akay).

PLIDA-SIM is entirely simulated.  It is not PLIDA data, not derived from PLIDA
data, and no PLIDA record contributed to it.  It imitates the *structure* of the
ABS PLIDA Modular Product so that the analytic workflow transfers, but every
value is generated from the equations below.  Parameter values were chosen for
pedagogical clarity, not to reproduce any real Australian estimate.  No result
produced from this dataset should be cited as evidence about any Australian
programme.

Design specification: PLIDA-SIM_design_spec.md v4.0

Usage
-----
    python make_data.py                          # primary dataset, CSV, ./plida_sim
    python make_data.py --variant B              # exercise variant
    python make_data.py --format both            # CSV + Parquet
    python make_data.py --no-truth               # withhold truth_parameters
    python make_data.py --n 5000 --outdir /tmp/x # small smoke-test build

Architecture
------------
Nine data modules plus a truth file.  Each module draws from its own random
stream, spawned from a single master seed via ``numpy.random.SeedSequence``.
That means a module can be re-parameterised and regenerated without disturbing
the realised values of any other module -- which matters when the book's
verified benchmark numbers depend on the treatment and outcome modules.

Everything is generated in **constant 2019 AUD** and inflated to nominal on the
way out (Section 7.5 of the spec).  A reader who deflates correctly recovers the
truth; a reader who does not, does not.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

DATASET_VERSION = "1.1.0"
SPEC_VERSION = "4.0"

YEARS = [2014, 2015, 2016, 2017, 2018, 2019]
BASELINE_YEAR = 2016      # t-1: covariates measured here
TREATMENT_YEAR = 2017     # t0
OUTCOME_YEAR = 2019       # t+2
INDEX_BASE_YEAR = 2019

VARIANT_SEEDS = {"A": 20260808, "B": 20260809}

# Random stream names, in a fixed order.  Append only -- never reorder, or every
# previously published figure in the book changes.
STREAMS = [
    "demographics", "locations", "capacity", "payments", "health",
    "treatment", "outcome", "attrition", "missingness", "presentation",
]

EDU_LABELS = ["<Year 12", "Year 12", "Cert III/IV", "Diploma", "Bachelor+"]
REMOTE_LABELS = ["Major Cities", "Inner Regional", "Outer Regional", "Remote+"]
COB_LABELS = ["Australia", "MESC", "Other"]
STATES = ["NSW", "VIC", "QLD", "SA", "WA", "TAS", "NT", "ACT"]
STATE_P = [0.31, 0.26, 0.20, 0.07, 0.10, 0.02, 0.01, 0.03]
PAYMENT_TYPES = ["Newstart", "Youth Allowance", "Parenting Payment", "DSP", "Carer"]
# Pre-treatment activity-requirement status, recorded in DOMINO for everyone.
# This is the legitimate near-instrument (spec Section 9.2).
MUTUAL_OBLIGATION = ["Exempt", "Partial", "Full", "Intensive"]
OCCUPATION_GROUPS = [
    "Managers", "Professionals", "Technicians and Trades",
    "Community and Personal Service", "Clerical and Administrative",
    "Sales", "Machinery Operators and Drivers", "Labourers",
]
# Pure outcome predictor: multiplicative earnings premium by occupation.
# Deliberately excluded from the treatment-assignment index (Section 9.2).
OCC_PREMIUM = np.array([0.34, 0.30, 0.10, -0.10, -0.02, -0.12, 0.04, -0.20])
OCC_P = np.array([0.08, 0.14, 0.14, 0.13, 0.14, 0.10, 0.08, 0.19])


@dataclass
class Config:
    n: int = 50_000
    variant: str = "A"
    seed: int | None = None
    outdir: Path = Path("plida_sim")
    fmt: str = "csv"
    with_truth: bool = True
    quiet: bool = False

    inflation_rate: float = 0.021          # ~2.1% p.a., both index series
    wpi_gap: float = 0.004                 # WPI runs slightly above CPI

    def resolved_seed(self) -> int:
        if self.seed is not None:
            return self.seed
        return VARIANT_SEEDS[self.variant]


def streams(seed: int) -> dict[str, np.random.Generator]:
    children = np.random.SeedSequence(seed).spawn(len(STREAMS))
    return {name: np.random.default_rng(ss) for name, ss in zip(STREAMS, children)}


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def log(cfg: Config, msg: str) -> None:
    if not cfg.quiet:
        print(msg, file=sys.stderr)


# ---------------------------------------------------------------------------
# 1. Latent world
# ---------------------------------------------------------------------------

def build_latent(cfg: Config, rng: dict) -> dict:
    """Everything true about each person, before any of it is observed."""
    n = cfg.n
    L: dict = {}

    # -- demographics -------------------------------------------------------
    g = rng["demographics"]
    L["person_id"] = np.array([f"PLIDASIM_{i:06d}" for i in range(1, n + 1)])
    age = g.integers(22, 60, n)                       # age at 31 Dec 2016
    L["age"] = age
    L["birth_year"] = BASELINE_YEAR - age
    L["female"] = g.binomial(1, 0.49, n)
    L["cob"] = g.choice([0, 1, 2], n, p=[0.68, 0.20, 0.12])
    L["edu"] = g.choice([0, 1, 2, 3, 4], n, p=[0.18, 0.22, 0.26, 0.13, 0.21])
    L["kids"] = g.binomial(3, 0.22 + 0.06 * L["female"], n)
    L["lang"] = g.binomial(1, np.where(L["cob"] == 2, 0.35, 0.03))
    # arrival year for the overseas-born, at least 2 years before baseline
    arrival = np.where(
        L["cob"] > 0,
        np.clip(L["birth_year"] + g.integers(1, 45, n), 1960, BASELINE_YEAR - 2),
        -1,
    )
    L["year_of_arrival"] = arrival
    L["occupation"] = g.choice(len(OCCUPATION_GROUPS), n, p=OCC_P)

    # -- geography ----------------------------------------------------------
    g = rng["locations"]
    L["remote"] = g.choice([0, 1, 2, 3], n, p=[0.72, 0.19, 0.07, 0.02])
    L["seifa"] = np.clip(
        g.normal(5.5 - 0.9 * L["remote"] + 0.55 * L["edu"], 2.4, n), 1, 10
    ).round().astype(int)
    L["state"] = g.choice(len(STATES), n, p=STATE_P)
    L["sa4_base"] = g.integers(101, 900, n)
    L["moves"] = g.random((n, len(YEARS))) < 0.035     # ~3.5% relocate per year

    # -- earnings capacity and the pre-period trajectory --------------------
    g = rng["capacity"]
    cap = (
        10.20
        + 0.16 * L["edu"]
        + 0.010 * (L["age"] - 40)
        - 0.00090 * (L["age"] - 40) ** 2
        - 0.11 * L["remote"]
        + 0.030 * L["seifa"]
        - 0.20 * L["lang"]
        - 0.12 * L["kids"]
        + OCC_PREMIUM[L["occupation"]]          # pure outcome predictor
        # Total latent dispersion is held at ~0.40 SD.  The occupation premium
        # contributes ~0.18, so the residual term is reduced accordingly:
        # sqrt(0.36^2 + 0.18^2) ~= 0.40.  Raising this materially inflates the
        # skew of y0, and every propensity method degrades sharply -- which is
        # Basu et al. (2008) in action, and is why this constant is not free.
        + g.normal(0, 0.36, n)
    )
    L["cap"] = cap

    inc2015 = np.exp(cap + g.normal(0, 0.28, n))
    inc2014 = inc2015 * np.exp(g.normal(-0.02, 0.22, n))

    # Ashenfelter dip: a pre-programme earnings shock in the baseline year
    shock = g.binomial(1, 0.30 + 0.10 * (L["edu"] <= 1), n)
    dip = np.where(shock == 1, g.uniform(0.25, 0.75, n), g.uniform(0.95, 1.10, n))
    inc2016 = inc2015 * dip * np.exp(g.normal(0, 0.20, n))
    L["shock"] = shock
    L["inc_real"] = {2014: inc2014, 2015: inc2015, 2016: inc2016}

    # -- income support history (DOMINO-style) ------------------------------
    g = rng["payments"]
    # Time on payment is a bounded count out of 26 fortnights, and in real
    # administrative data it is heavily over-dispersed and bimodal: many short
    # spells, and a substantial block on payment for the whole year. A Poisson
    # has neither property -- it put 0.2% of the population above 20 fortnights
    # and essentially nobody at 26, which no one who has seen DOMINO would
    # believe. A beta-binomial gives the right shape at the same coverage.
    lin = (-0.55 + 1.30 * shock + 0.35 * (L["edu"] <= 1) + 0.22 * L["remote"]
           - 0.055 * L["seifa"] - 0.000012 * inc2016)
    mu = sigmoid(lin)
    conc = 1.0                      # lower means more mass at both ends
    p_pay = g.beta(np.clip(mu * conc, 1e-3, None),
                   np.clip((1 - mu) * conc, 1e-3, None))
    fn2016 = g.binomial(26, p_pay)
    L["fn2016"] = fn2016
    L["lts"] = (fn2016 >= 20).astype(int)
    # a plausible primary payment type given circumstances
    ptype = np.where(
        L["kids"] >= 2, 2,
        np.where(L["age"] < 25, 1, np.where(g.random(n) < 0.10, 3, 0)),
    )
    ptype = np.where((g.random(n) < 0.05) & (L["kids"] > 0), 4, ptype)
    L["payment_type"] = ptype
    L["second_payment"] = g.random(n) < 0.12
    L["fn_hist_noise"] = g.normal(0, 1.0, (n, len(YEARS)))
    L["mo_noise"] = g.random(n)

    # -- health (MBS / PBS-style) -------------------------------------------
    g = rng["health"]
    L["gp"] = g.poisson(
        np.exp(0.9 + 0.012 * (L["age"] - 40) + 0.28 * L["female"] + 0.20 * shock)
    )
    L["mh"] = g.binomial(1, sigmoid(-2.3 + 0.9 * shock + 0.5 * L["lts"]))
    L["pbs"] = g.poisson(np.exp(0.5 + 0.020 * (L["age"] - 40) + 0.9 * L["mh"]))
    L["health_year_noise"] = g.random((n, len(YEARS)))

    # -- treatment assignment ------------------------------------------------
    g = rng["treatment"]
    # Caseworker-assessed employability: recorded nowhere, correlated with
    # nothing observable, and consequential for both referral and earnings.
    # This is the U that Chapter 10's sensitivity analysis is about. The
    # earnings shock cannot play that role, because the earnings trajectory in
    # the analysis file is a direct observable trace of it -- the covariates
    # already explain 58% of it, leaving almost nothing to reveal.
    L["u_employability"] = g.normal(0, 1, n)
    # Rescaled with the fortnights distribution: lts now describes ~23% of the
    # sample rather than 0.2%, so the coefficient on it must come down to keep
    # mandatory referral the small, concentrated group the overlap failure needs.
    mand = g.binomial(1, sigmoid(-4.50 + 0.95 * L["lts"] + 0.8 * L["remote"] + 0.6 * L["mh"]))
    # Mutual obligation status is a *pre-treatment* attribute of the person's
    # income support arrangement, recorded in DOMINO for everyone -- treated or
    # not.  It is the observable proxy for `mand`, and the legitimate
    # near-instrument of Section 9.2.  Strong but deliberately imperfect: if it
    # predicted treatment exactly, the propensity model would separate and the
    # exercise would collapse rather than teach.
    u = L["mo_noise"]
    mo = np.where(
        mand == 1,
        np.where(u < 0.85, 3, 2),                          # Intensive / Full
        np.where(u < 0.004, 3, np.where(u < 0.21, 2, np.where(u < 0.64, 1, 0))),
    )
    L["mutual_obligation"] = mo
    idx = (
        -2.48
        + 0.016 * fn2016
        + 0.40 * shock
        + 0.24 * (L["edu"] <= 1)
        - 0.42 * (L["edu"] == 4)
        - 0.055 * L["seifa"]
        + 0.20 * L["remote"]
        + 0.35 * L["mh"]
        - 0.0000048 * inc2016
        - 0.018 * (L["age"] - 40)
        + 0.25 * L["lang"]
        - 0.16 * L["u_employability"]   # unmeasured; see Chapter 10
        + 4.60 * mand                    # manufactures the common-support failure
    )
    L["mand"] = mand
    L["ps_true"] = sigmoid(idx)
    L["D"] = g.binomial(1, L["ps_true"])
    L["commence_day"] = g.integers(0, 365, n)
    L["stream"] = g.choice([0, 1, 2], n, p=[0.45, 0.35, 0.20])
    L["weeks_in_program"] = np.clip(g.poisson(26 + 8 * L["stream"]), 4, 104)

    # -- potential outcomes ---------------------------------------------------
    g = rng["outcome"]
    tau = (
        2600
        + 4400 * shock
        + 2400 * (L["edu"] <= 1)
        + 520 * L["lts"]
        - 38 * (L["age"] - 40)
        + g.normal(0, 1000, n)
    )
    tau = np.clip(tau, -2500, None)
    y0 = np.exp(
        cap
        + 0.07 * L["u_employability"]   # the same U, on the outcome side
        + 0.28 * np.log(np.clip(inc2016, 500, None) / 40000)
        - 0.0068 * fn2016
        - 0.12 * L["mh"]
        + g.normal(0, 0.30, n)
    )
    y0 = np.clip(y0, 0, None)
    L["tau"] = tau
    L["y0"] = y0
    L["y1"] = y0 + tau
    L["inc_real"][OUTCOME_YEAR] = y0 + tau * L["D"]

    # interim years: participation displaces work in t0, effect part-realised in t+1
    lock_in = 1.0 - 0.25 * L["D"]
    L["inc_real"][2017] = np.clip(
        (0.55 * inc2016 + 0.45 * L["inc_real"][OUTCOME_YEAR])
        * lock_in * np.exp(g.normal(0, 0.18, n)), 0, None
    )
    L["inc_real"][2018] = np.clip(
        (y0 + 0.55 * tau * L["D"]) * np.exp(g.normal(0, 0.16, n)), 0, None
    )

    return L


# ---------------------------------------------------------------------------
# 2. Attrition  (spec Section 7.4)
# ---------------------------------------------------------------------------

def apply_attrition(cfg: Config, rng: dict, L: dict) -> dict:
    """Three exit routes, only two of them labelled in the delivered data."""
    g = rng["attrition"]
    n = cfg.n

    p_die = sigmoid(-5.3 + 0.055 * (L["age"] - 40) + 1.1 * L["mh"]
                    + 0.11 * (11 - L["seifa"]) + 0.6 * L["shock"])
    p_emi = sigmoid(-4.8 + 1.8 * (L["cob"] > 0) + 0.9 * (L["edu"] >= 3)
                    - 0.45 * L["kids"] - 0.9 * L["lts"])
    # The coefficient on lts is much smaller than it looks: lts now describes
    # about a quarter of the sample rather than a fifth of a per cent, so the
    # same total attrition needs far less weight on it.
    p_lost = sigmoid(-3.75 + 0.55 * L["lts"] + 1.75 * L["shock"]
                     + 0.45 * L["remote"] + 0.5 * L["mh"])

    died = g.binomial(1, p_die).astype(bool)
    emig = g.binomial(1, p_emi).astype(bool) & ~died
    lost = g.binomial(1, p_lost).astype(bool) & ~died & ~emig

    # Exits are spread over the post-treatment window 2017-2019.
    exit_year = g.choice([2017, 2018, 2019], n, p=[0.30, 0.34, 0.36])

    reason = np.full(n, "", dtype=object)
    reason[died] = "deceased"
    reason[emig] = "emigrated"
    reason[lost] = "out_of_scope"
    attrited = died | emig | lost

    L["attrited"] = attrited
    L["attrition_reason"] = np.where(attrited, reason, "")
    L["attrition_year"] = np.where(attrited, exit_year, -1)
    L["deceased_year"] = np.where(died, exit_year, -1)
    L["emigrated_year"] = np.where(emig, exit_year, -1)
    L["last_active_year"] = np.where(attrited, exit_year - 1, OUTCOME_YEAR)
    return L


# ---------------------------------------------------------------------------
# 3. Indexation  (spec Section 7.5)
# ---------------------------------------------------------------------------

def index_table(cfg: Config) -> pd.DataFrame:
    rows = []
    for y in YEARS:
        k = y - INDEX_BASE_YEAR
        rows.append({
            "ref_year": y,
            "cpi_index": round(100.0 * (1 + cfg.inflation_rate) ** k, 2),
            "wpi_index": round(100.0 * (1 + cfg.inflation_rate + cfg.wpi_gap) ** k, 2),
        })
    return pd.DataFrame(rows)


def to_nominal(real_value, year: int, idx: pd.DataFrame, series: str = "cpi_index"):
    factor = float(idx.loc[idx.ref_year == year, series].iloc[0]) / 100.0
    return real_value * factor


# ---------------------------------------------------------------------------
# 4. Module builders
# ---------------------------------------------------------------------------

def build_spine(L: dict) -> pd.DataFrame:
    df = pd.DataFrame({"person_id": L["person_id"]})
    for y in YEARS:
        df[f"in_scope_{y}"] = np.where(
            (L["attrition_year"] > 0) & (y >= L["attrition_year"]), 0, 1
        ).astype(int)
    df["deceased_year"] = np.where(L["deceased_year"] > 0, L["deceased_year"], pd.NA)
    df["emigrated_year"] = np.where(L["emigrated_year"] > 0, L["emigrated_year"], pd.NA)
    df["last_active_year"] = L["last_active_year"]
    return df


def build_demographics(L: dict) -> pd.DataFrame:
    return pd.DataFrame({
        "person_id": L["person_id"],
        "birth_year": L["birth_year"],
        "sex": np.where(L["female"] == 1, "Female", "Male"),
        "country_of_birth_group": np.array(COB_LABELS)[L["cob"]],
        "year_of_arrival": np.where(L["year_of_arrival"] > 0, L["year_of_arrival"], pd.NA),
    })


def build_locations(cfg: Config, rng: dict, L: dict) -> pd.DataFrame:
    g = rng["presentation"]
    n = cfg.n
    frames = []
    sa4 = L["sa4_base"].copy()
    seifa = L["seifa"].astype(float).copy()
    for j, y in enumerate(YEARS):
        movers = L["moves"][:, j]
        sa4 = np.where(movers, np.clip(sa4 + g.integers(-40, 41, n), 101, 899), sa4)
        seifa = np.where(movers, np.clip(seifa + g.integers(-1, 2, n), 1, 10), seifa)
        frames.append(pd.DataFrame({
            "person_id": L["person_id"],
            "ref_year": y,
            "state": np.array(STATES)[L["state"]],
            "remoteness_area": np.array(REMOTE_LABELS)[L["remote"]],
            "sa4_code": [f"{c:03d}" for c in sa4],
            "seifa_irsd_decile": seifa.astype(int),
        }))
    df = pd.concat(frames, ignore_index=True)
    return df.sort_values(["person_id", "ref_year"], ignore_index=True)


def build_census(cfg: Config, rng: dict, L: dict) -> pd.DataFrame:
    g = rng["missingness"]
    n = cfg.n
    inc16 = L["inc_real"][2016]
    lfs = np.where(
        inc16 > 55000, "Employed FT",
        np.where(inc16 > 18000, "Employed PT",
                 np.where(L["fn2016"] >= 8, "Unemployed", "NILF")),
    )
    fam = np.where(
        L["kids"] == 0,
        np.where(g.random(n) < 0.45, "Couple", "Lone person"),
        np.where(g.random(n) < 0.62, "Couple", "Lone parent"),
    )
    fam = np.where(g.random(n) < 0.04, "Other", fam)

    df = pd.DataFrame({
        "person_id": L["person_id"],
        "highest_edu": np.array(EDU_LABELS)[L["edu"]],
        "labour_force_status_2016": lfs,
        "english_proficiency": np.where(L["lang"] == 1, "Not well", "Well"),
        "dependent_children": L["kids"],
        "family_composition": fam,
    })

    # Census non-response: the whole person record is absent (MAR on remoteness,
    # English proficiency and country of birth -- all observable elsewhere).
    p_nr = sigmoid(-3.0 + 0.55 * L["remote"] + 1.1 * L["lang"] + 0.30 * (L["cob"] == 2))
    responded = g.binomial(1, 1 - p_nr).astype(bool)
    return df.loc[responded].reset_index(drop=True)


def build_pit(cfg: Config, rng: dict, L: dict, idx: pd.DataFrame) -> pd.DataFrame:
    g = rng["missingness"]
    gp = rng["presentation"]
    n = cfg.n
    frames = []
    for y in YEARS:
        real = L["inc_real"][y]
        active = ~((L["attrition_year"] > 0) & (y >= L["attrition_year"]))

        # MNAR: low earners do not lodge, so their row is simply absent.
        p_nonlodge = sigmoid(0.5 - 0.00012 * real)
        lodged = g.binomial(1, 1 - p_nonlodge).astype(bool)
        keep = active & lodged
        if keep.sum() == 0:
            continue

        wages = to_nominal(real[keep], y, idx)
        other = np.clip(gp.normal(0, 900, keep.sum()) + 300 * (real[keep] > 60000), 0, None)
        occ = np.where(real[keep] > 1000, np.array(OCCUPATION_GROUPS)[L["occupation"][keep]], None)

        frames.append(pd.DataFrame({
            "person_id": L["person_id"][keep],
            "ref_year": y,
            "salary_wages_nominal": np.round(wages, 0),
            "total_income_nominal": np.round(wages + other, 0),
            "occupation_group": occ,
        }))
    df = pd.concat(frames, ignore_index=True)
    return df.sort_values(["person_id", "ref_year"], ignore_index=True)


def build_payments(cfg: Config, rng: dict, L: dict, idx: pd.DataFrame) -> pd.DataFrame:
    g = rng["payments"]
    n = cfg.n
    frames = []
    for j, y in enumerate(YEARS):
        active = ~((L["attrition_year"] > 0) & (y >= L["attrition_year"]))
        # fortnights drift around the 2016 anchor; participants exit support faster
        drift = L["fn_hist_noise"][:, j] * 2.0
        trend = np.where(
            y <= BASELINE_YEAR, -0.8 * (BASELINE_YEAR - y),
            -1.6 * (y - BASELINE_YEAR) - 2.2 * L["D"] * (y > TREATMENT_YEAR),
        )
        fn = np.clip(np.round(L["fn2016"] + drift + trend), 0, 26).astype(int)
        keep = active & (fn > 0)
        if keep.sum() == 0:
            continue
        rate = 620 + 90 * L["kids"][keep] + 140 * (L["payment_type"][keep] == 3)
        frames.append(pd.DataFrame({
            "person_id": L["person_id"][keep],
            "ref_year": y,
            "payment_type": np.array(PAYMENT_TYPES)[L["payment_type"][keep]],
            "fortnights_on_payment": fn[keep],
            "payment_amount_nominal": np.round(to_nominal(fn[keep] * rate, y, idx), 0),
            "mutual_obligation_status": np.array(MUTUAL_OBLIGATION)[L["mutual_obligation"][keep]],
        }))
        # A minority also draw a second payment type in the same year. It must
        # differ from their primary type, or the module violates its own
        # declared grain of person x year x payment type -- which the audit
        # checks, and which would break any reader's groupby.
        sec = keep & L["second_payment"] & (fn >= 6)
        if sec.sum() > 0:
            fn2 = np.clip(np.round(fn[sec] * g.uniform(0.2, 0.6, sec.sum())), 1, 26).astype(int)
            second_type = np.where(L["payment_type"][sec] == 4, 0, 4)  # Carer, else Newstart
            frames.append(pd.DataFrame({
                "person_id": L["person_id"][sec],
                "ref_year": y,
                "payment_type": np.array(PAYMENT_TYPES)[second_type],
                "fortnights_on_payment": fn2,
                "payment_amount_nominal": np.round(to_nominal(fn2 * 500, y, idx), 0),
                "mutual_obligation_status": np.array(MUTUAL_OBLIGATION)[L["mutual_obligation"][sec]],
            }))
    df = pd.concat(frames, ignore_index=True)
    return df.sort_values(["person_id", "ref_year", "payment_type"], ignore_index=True)


def build_health(cfg: Config, rng: dict, L: dict) -> pd.DataFrame:
    g = rng["health"]
    frames = []
    for j, y in enumerate(YEARS):
        active = ~((L["attrition_year"] > 0) & (y >= L["attrition_year"]))
        gp_y = g.poisson(np.clip(L["gp"] * (0.85 + 0.3 * L["health_year_noise"][:, j]), 0, None))
        # structural absence: no service contact in the year means no row at all
        keep = active & (gp_y > 0)
        if keep.sum() == 0:
            continue
        frames.append(pd.DataFrame({
            "person_id": L["person_id"][keep],
            "ref_year": y,
            "gp_attendances": gp_y[keep],
            "mh_item_flag": (L["mh"][keep] & (g.random(keep.sum()) < 0.8)).astype(int),
            "pbs_scripts": g.poisson(np.clip(L["pbs"][keep] * 0.9, 0, None)),
        }))
    df = pd.concat(frames, ignore_index=True)
    return df.sort_values(["person_id", "ref_year"], ignore_index=True)


def build_program(L: dict) -> pd.DataFrame:
    """Participants only.

    Note that every column here is observed *only for the treated*, which makes
    all of them post-treatment variables.  `referral_type` in particular looks
    like a useful covariate and is a perfect predictor of treatment, because
    controls have no row at all.  A reader who joins it into the propensity
    model gets separation.  That failure is deliberate and is the subject of a
    Chapter 3 exercise; the legitimate pre-treatment version of the same
    construct is `mutual_obligation_status` in `domino_payments`.
    """
    t = L["D"] == 1
    start = pd.Timestamp(f"{TREATMENT_YEAR}-01-01") + pd.to_timedelta(L["commence_day"][t], unit="D")
    return pd.DataFrame({
        "person_id": L["person_id"][t],
        "commencement_date": start.strftime("%Y-%m-%d"),
        "referral_type": np.where(L["mand"][t] == 1, "Mandatory", "Voluntary"),
        "service_stream": np.array(["Stream A", "Stream B", "Stream C"])[L["stream"][t]],
        "weeks_in_program": L["weeks_in_program"][t],
    }).sort_values("person_id", ignore_index=True)


def build_truth(L: dict) -> pd.DataFrame:
    return pd.DataFrame({
        "person_id": L["person_id"],
        "true_propensity": np.round(L["ps_true"], 6),
        "y0": np.round(L["y0"], 2),
        "y1": np.round(L["y1"], 2),
        "tau_i": np.round(L["tau"], 2),
        "treated": L["D"],
        "earnings_shock_2016": L["shock"],
        "u_employability": np.round(L["u_employability"], 4),
        "attrited": L["attrited"].astype(int),
        "attrition_reason": L["attrition_reason"],
    })


# ---------------------------------------------------------------------------
# 5. Assembly and output
# ---------------------------------------------------------------------------

def generate(cfg: Config) -> dict[str, pd.DataFrame]:
    seed = cfg.resolved_seed()
    rng = streams(seed)
    log(cfg, f"PLIDA-SIM {DATASET_VERSION} | variant {cfg.variant} | seed {seed} | n={cfg.n:,}")

    L = build_latent(cfg, rng)
    L = apply_attrition(cfg, rng, L)
    idx = index_table(cfg)

    frames = {
        "spine_scoping": build_spine(L),
        "core_demographics": build_demographics(L),
        "core_locations": build_locations(cfg, rng, L),
        "census16_person": build_census(cfg, rng, L),
        "pit_income": build_pit(cfg, rng, L, idx),
        "domino_payments": build_payments(cfg, rng, L, idx),
        "mbs_pbs_health": build_health(cfg, rng, L),
        "epp_program": build_program(L),
        "reference_indices": idx,
    }
    if cfg.with_truth:
        frames["truth_parameters"] = build_truth(L)
    return frames


def write(cfg: Config, frames: dict[str, pd.DataFrame]) -> None:
    root = cfg.outdir
    root.mkdir(parents=True, exist_ok=True)
    (root / "truth").mkdir(parents=True, exist_ok=True)

    manifest = {
        "dataset": "PLIDA-SIM",
        "dataset_version": DATASET_VERSION,
        "spec_version": SPEC_VERSION,
        "variant": cfg.variant,
        "seed": cfg.resolved_seed(),
        "n_persons": cfg.n,
        "years": YEARS,
        "treatment_year": TREATMENT_YEAR,
        "outcome_year": OUTCOME_YEAR,
        "index_base_year": INDEX_BASE_YEAR,
        "currency": "AUD nominal; deflate with reference_indices.csv",
        "files": {},
        "disclaimer": (
            "Entirely simulated. Not PLIDA data and not derived from PLIDA data. "
            "No result from this dataset is evidence about any Australian programme."
        ),
    }

    for name, df in frames.items():
        target = root / "truth" if name == "truth_parameters" else root
        if cfg.fmt in ("csv", "both"):
            df.to_csv(target / f"{name}.csv", index=False)
        if cfg.fmt in ("parquet", "both"):
            try:
                df.to_parquet(target / f"{name}.parquet", index=False)
            except ImportError:
                raise SystemExit(
                    "Parquet output needs a parquet engine that is not installed.\n"
                    "  pip install pyarrow\n"
                    "Or generate CSV instead with --format csv."
                )
        manifest["files"][name] = {"rows": int(len(df)), "columns": list(df.columns)}
        log(cfg, f"  {name:<20} {len(df):>9,} rows")

    (root / "manifest.json").write_text(json.dumps(manifest, indent=2))

    if not cfg.with_truth:
        # A reader who goes looking for the truth file should find an
        # explanation rather than an empty folder or nothing at all.
        (root / "truth" / "README.md").write_text(
            "# Withheld deliberately\n\n"
            "`truth_parameters.csv` is not included in this build.\n\n"
            "This is the exercise variant. It holds both potential outcomes for\n"
            "every person, so shipping it would let end-of-chapter answers be\n"
            "looked up rather than worked out.\n\n"
            "To generate it yourself for a dataset you are experimenting with:\n\n"
            "    python make_data.py --variant B --outdir somewhere_else\n\n"
            "Instructors can request the file for the published variant B.\n"
        )
        log(cfg, "  truth_parameters withheld (--no-truth)")
        return

    (root / "truth" / "README.md").write_text(
        "# Do not use these files in the analysis\n\n"
        "`truth_parameters` contains both potential outcomes for every person.\n"
        "It exists only because this is a teaching dataset. Joining it into an\n"
        "analysis defeats the purpose of every exercise in the book.\n\n"
        "Use it at the *end* of a chapter, to score an estimate you have already\n"
        "produced without it.\n\n"
        "| Column | Meaning |\n| --- | --- |\n"
        "| `true_propensity` | True P(D=1 \\| X) from the assignment equation |\n"
        "| `y0`, `y1` | Both potential outcomes, 2019 income, constant 2019 AUD |\n"
        "| `tau_i` | Individual treatment effect, `y1 - y0` |\n"
        "| `earnings_shock_2016` | Unobserved confounder 1: the pre-programme "
        "earnings shock. Drives take-up, the outcome and attrition |\n"
        "| `u_employability` | Unobserved confounder 2: a latent employability "
        "trait, in no reader-visible module. Both are Chapter 10's subject |\n"
        "| `attrited`, `attrition_reason` | Whether and why the person left before 2019 |\n"
    )


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Generate the PLIDA-SIM synthetic dataset.")
    p.add_argument("--n", type=int, default=50_000, help="number of persons")
    p.add_argument("--variant", choices=["A", "B"], default="A",
                   help="A = worked examples, B = end-of-chapter exercises")
    p.add_argument("--seed", type=int, default=None, help="override the variant seed")
    p.add_argument("--outdir", type=Path, default=None)
    p.add_argument("--format", dest="fmt", choices=["csv", "parquet", "both"], default="csv")
    p.add_argument("--no-truth", action="store_true", help="withhold truth_parameters")
    p.add_argument("--quiet", action="store_true")
    a = p.parse_args(argv)

    outdir = a.outdir or Path(f"plida_sim_{a.variant.lower()}")
    cfg = Config(n=a.n, variant=a.variant, seed=a.seed, outdir=outdir,
                 fmt=a.fmt, with_truth=not a.no_truth, quiet=a.quiet)

    frames = generate(cfg)
    write(cfg, frames)
    log(cfg, f"Written to {cfg.outdir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
