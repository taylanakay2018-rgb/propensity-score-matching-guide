#!/usr/bin/env python3
"""
Script 2.5 — Linking the modules
=================================
Chapter 2, Section 2.5. Produces Table 2.4; Table 2.3 comes from Script 2.1.

Builds the 2016 person-level file from the spine outwards, and demonstrates
the three failures that produce no error message: duplication through grain
mismatch, loss through inner joins, and treating a structural zero as unknown.

    python ch02/02_05_link_modules.py
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common import (cli, load, banner, safe_merge, BASELINE_YEAR,
                     occupation_carried_forward, mutual_obligation_dominant)
import pandas as pd

B = BASELINE_YEAR

def main():
    a = cli(__doc__)
    d = load(a.datadir)
    n = len(d["spine_scoping"])

    # ---- the three failures ------------------------------------------------
    banner("Failure 1 — duplication through grain mismatch")
    dom = d["domino_payments"].query("ref_year == @B")
    bad = d["core_demographics"].merge(dom, on="person_id", how="left")
    dup = (dom.groupby("person_id").size() > 1).sum()
    print(f"  domino_payments 2016: {len(dom):,} rows for {dom.person_id.nunique():,} persons")
    print(f"  naive merge          : {len(bad):,} rows for {n:,} people "
          f"(+{len(bad)-n:,}, {100*(len(bad)-n)/n:.1f}%)")
    print(f"  persons duplicated   : {dup:,}")

    banner("Failure 2 — loss through inner joins")
    inner = (d["core_demographics"][["person_id"]]
             .merge(d["pit_income"].query("ref_year == @B")[["person_id"]], on="person_id")
             .merge(d["census16_person"][["person_id"]], on="person_id")
             .merge(d["mbs_pbs_health"].query("ref_year == @B")[["person_id"]], on="person_id"))
    prog = set(d["epp_program"].person_id); kept = set(inner.person_id)
    print(f"  retained             : {len(inner):,} of {n:,} ({100*len(inner)/n:.1f}%)")
    print(f"  treated share        : {100*len(prog)/n:.2f}%  ->  {100*len(prog & kept)/len(kept):.2f}%")
    print("  See Section 2.5.2 for what this costs in effect terms: not much bias,")
    print("  and a thirty per cent change in who the estimate is about.")

    banner("Failure 3 — structural zeros treated as unknown")
    hl = d["mbs_pbs_health"].query("ref_year == @B")
    absent = n - hl.person_id.nunique()
    with_zeros = hl.gp_attendances.sum() / n
    print(f"  persons with no health row : {absent:,} ({100*absent/n:.1f}%)")
    print(f"  mean GP attendances, zeros filled  : {with_zeros:.2f}")
    print(f"  mean GP attendances, absent dropped: {hl.gp_attendances.mean():.2f}  "
          f"(+{100*(hl.gp_attendances.mean()-with_zeros)/with_zeros:.0f}%)")

    # ---- the correct build -------------------------------------------------
    banner("Table 2.4 — building the analysis file, step by step")
    log = []
    A = d["spine_scoping"][["person_id"]].copy()
    log.append(("Start from spine_scoping", len(A), A.person_id.nunique()))

    for label, frame in [
        ("+ core_demographics", d["core_demographics"]),
        ("+ census16_person", d["census16_person"]),
        ("+ core_locations, 2016 only",
         d["core_locations"].query("ref_year == @B").drop(columns="ref_year")),
        ("+ pit_income, 2016 only",
         d["pit_income"].query("ref_year == @B").drop(columns="ref_year")),
    ]:
        A = safe_merge(A, frame)
        log.append((label, len(A), A.person_id.nunique()))

    totals = dom.groupby("person_id", as_index=False).agg(
        fortnights=("fortnights_on_payment", "sum"),
        payment_amount_nominal=("payment_amount_nominal", "sum"))
    # The activity-requirement level is categorical, so it cannot be summed.
    # Where a person holds more than one payment type in the year, take the
    # status attached to the type they were on longest. This is the
    # near-instrument of Section 2.4.4 and Chapter 3 needs it, so it has to
    # survive the aggregation rather than be dropped by it.
    dominant = (mutual_obligation_dominant(dom, index=A["person_id"])
                .rename("mutual_obligation_status").reset_index())
    A = safe_merge(A, totals)
    A = safe_merge(A, dominant)
    log.append(("+ domino_payments, aggregated", len(A), A.person_id.nunique()))

    A = safe_merge(A, hl.drop(columns="ref_year"))
    log.append(("+ mbs_pbs_health, 2016 only", len(A), A.person_id.nunique()))

    A["treated"] = A["person_id"].isin(d["epp_program"]["person_id"]).astype(int)
    log.append(("+ treatment flag", len(A), A.person_id.nunique()))

    # Occupation carried forward from the most recent pre-period year in which
    # it is observed. Taking 2016 alone would tie it to the non-lodger
    # mechanism; see Section 2.6.3.
    A = A.drop(columns=["occupation_group"], errors="ignore")
    A = safe_merge(A, occupation_carried_forward(d["pit_income"])
                   .rename("occupation_group").reset_index())
    log.append(("+ occupation, carried forward", len(A), A.person_id.nunique()))

    age = B - A["birth_year"]
    on_support = set(d["domino_payments"].query("ref_year in [2015, 2016]").person_id)
    in_scope = set(d["spine_scoping"].query("in_scope_2016 == 1").person_id)
    A["eligible"] = (age.between(22, 59)
                     & A["person_id"].isin(on_support)
                     & A["person_id"].isin(in_scope)).astype(int)
    log.append(("+ eligibility flag", len(A), A.person_id.nunique()))

    print(f"  {'Step':32s} {'Rows':>8s} {'Persons':>9s}")
    for label, r, p in log:
        print(f"  {label:32s} {r:>8,} {p:>9,}")

    # structural zeros
    for c in ("gp_attendances", "mh_item_flag", "pbs_scripts", "fortnights"):
        A[c] = A[c].fillna(0)

    print(f"\n  {A.shape[1]} columns · {A.treated.sum():,} participants "
          f"({100*A.treated.mean():.2f}%) · {A.eligible.sum():,} eligible "
          f"({100*A.eligible.mean():.1f}%)")
    print(f"  participants outside the eligibility rule: "
          f"{int(((A.treated == 1) & (A.eligible == 0)).sum()):,}  (see Section 2.2.4)")

    out = a.datadir / "linked_2016.csv"
    A.to_csv(out, index=False)
    print(f"\n  written to {out}")

if __name__ == "__main__":
    main()
