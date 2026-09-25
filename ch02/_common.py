"""
Shared helpers for the Chapter 2 scripts.

Every script in this folder is standalone and runnable from a clean checkout.
They share only this module, which handles locating the data and the two or
three operations that would otherwise be copied into all nine.
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

BASELINE_YEAR = 2016
TREATMENT_YEAR = 2017
OUTCOME_YEAR = 2019
YEARS = [2014, 2015, 2016, 2017, 2018, 2019]

REPO = Path(__file__).resolve().parent.parent
DEFAULT_DATA = REPO / "plida_sim" / "plida_sim_a"

MODULES = [
    "spine_scoping", "core_demographics", "core_locations", "census16_person",
    "pit_income", "domino_payments", "mbs_pbs_health", "epp_program",
    "reference_indices",
]


def cli(description: str) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--datadir", type=Path, default=DEFAULT_DATA,
                   help="folder holding the PLIDA-SIM CSV files")
    p.add_argument("--outdir", type=Path, default=REPO / "figures")
    # Accepted by every script so continuous integration can call them all the
    # same way. Only the two that repeat across draws actually use it.
    p.add_argument("--quick", action="store_true",
                   help="fewer draws where a script repeats an experiment")
    # Script 2.4 only. Accepted everywhere so the scripts share one CLI.
    p.add_argument("--placement", action="store_true",
                   help="Script 2.4: also produce Table 2.2 (six draws, ~4 min)")
    # Chapters 3 and 4: which propensity score estimator to work from.
    p.add_argument("--estimator", choices=["logit", "gbm"], default="logit",
                   help="propensity score estimator (default: logit)")
    p.add_argument("--rule", default=None,
                   help="Script 4.4: which trimming rule to describe")
    return p.parse_args()


# Rough coverage each module should have, as a share of the spine. Used only
# to catch a truncated or partial download, which otherwise produces plausible
# looking output from a quarter of the data.
MIN_COVERAGE = {
    "core_demographics": 0.99, "core_locations": 0.99, "census16_person": 0.80,
    "pit_income": 0.70, "domino_payments": 0.40, "mbs_pbs_health": 0.60,
}


def load(datadir: Path = DEFAULT_DATA, with_truth: bool = False,
         check: bool = True) -> dict:
    """Read the modules, with the checks a careful analyst would run first.

    Fails with a message rather than a traceback when the data are absent,
    truncated, or missing the truth file a script needs.
    """
    if not datadir.exists():
        sys.exit(
            f"No data at {datadir}.\n"
            f"Generate it first:  python make_data.py --outdir {datadir}"
        )
    missing = [m for m in MODULES if not (datadir / f"{m}.csv").exists()]
    if missing:
        sys.exit(f"{datadir} is missing: {', '.join(missing)}\n"
                 f"Regenerate it:  python make_data.py --outdir {datadir}")

    d = {m: pd.read_csv(datadir / f"{m}.csv") for m in MODULES}

    if check:
        n = len(d["spine_scoping"])
        thin = []
        for m, floor in MIN_COVERAGE.items():
            cov = d[m]["person_id"].nunique() / n
            if cov < floor * 0.5:
                thin.append(f"{m} covers {cov:.1%} of the spine, expected about {floor:.0%}")
        if thin:
            sys.exit("These modules look truncated:\n  " + "\n  ".join(thin) +
                     f"\nRe-download or regenerate:  python make_data.py --outdir {datadir}")

    if with_truth:
        tp = datadir / "truth" / "truth_parameters.csv"
        if not tp.exists():
            sys.exit(
                f"This script needs {tp.name}, which is not in {datadir}.\n\n"
                "The exercise variant ships without it on purpose, so that\n"
                "end-of-chapter answers cannot be looked up. Use the primary\n"
                "dataset, or generate a copy with the truth file included:\n\n"
                f"    python make_data.py --outdir {datadir.parent / 'plida_sim_a'}"
            )
        d["truth"] = pd.read_csv(tp)
    return d


def safe_merge(left: pd.DataFrame, right: pd.DataFrame, on: str = "person_id"):
    """A merge that refuses to duplicate rows. See Section 2.5.4."""
    n_before = len(left)
    if not right[on].is_unique:
        raise ValueError(f"right side is not one row per {on}")
    out = left.merge(right, on=on, how="left", validate="one_to_one")
    if len(out) != n_before:
        raise ValueError(f"row count changed: {n_before} -> {len(out)}")
    return out


def deflate(df: pd.DataFrame, indices: pd.DataFrame, cols, series="cpi_index"):
    """Nominal to constant dollars of the index base year. See Section 2.6.5."""
    out = df.merge(indices[["ref_year", series]], on="ref_year", how="left")
    for c in cols:
        out[c.replace("_nominal", "_real")] = out[c] / (out[series] / 100.0)
    return out.drop(columns=[series])


def occupation_carried_forward(pit, years=(2014, 2015, 2016)):
    """Occupation from the most recent pre-period year in which it is observed.

    Taking it from 2016 alone ties it to the non-lodger mechanism: it is null
    for exactly the people with no 2016 tax record and for nobody else, which
    turns the 'unknown' level into a copy of the missingness indicator. Carrying
    the most recent observed value forward is standard practice with
    administrative data and decouples the two.
    """
    out = None
    for y in years:                      # earliest first, later years overwrite
        s = (pit.query("ref_year == @y").set_index("person_id")["occupation_group"]
             .dropna())
        out = s if out is None else s.combine_first(out)
    return out


NOT_ON_PAYMENT = "Not on payment"


def mutual_obligation_dominant(dom, index=None):
    """Activity-requirement status at person level, for one reference year.

    The status is categorical, so aggregating a person's payment types cannot
    sum it; we take the status attached to the type they were on longest.

    Persons with no payment row in the year get their own category rather than
    being folded into "Exempt". The two are different things: an exempt
    recipient is on payment with no activity requirement, whereas a person with
    no row was not on payment at all. Folding them together is the structural
    zero mistake of Section 2.5.2 committed on a categorical variable, and it
    is not harmless here -- the two groups commence the programme at 9.3 and
    6.7 per cent respectively.
    """
    out = (dom.sort_values("fortnights_on_payment", ascending=False)
           .drop_duplicates("person_id")
           .set_index("person_id")["mutual_obligation_status"])
    if index is not None:
        out = out.reindex(index)
    return out.fillna(NOT_ON_PAYMENT)


def smd(v: np.ndarray, a: np.ndarray, b: np.ndarray) -> float:
    """Standardised mean difference between two boolean-indexed groups."""
    pooled = np.sqrt((v[a].var() + v[b].var()) / 2)
    return float((v[a].mean() - v[b].mean()) / pooled) if pooled > 0 else 0.0


def banner(title: str) -> None:
    print("\n" + title)
    print("-" * len(title))
