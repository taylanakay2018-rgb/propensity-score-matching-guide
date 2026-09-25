#!/usr/bin/env python3
"""
Script 2.1 — Load and profile the nine modules
===============================================
Chapter 2, Section 2.5.1. Produces Table 2.3.

Reads every PLIDA-SIM module and reports its grain, its row count and its
person coverage. Run this first: if it does not work, nothing else will.

    python ch02/02_01_load_modules.py
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common import cli, load, banner, MODULES, BASELINE_YEAR
import pandas as pd

def main():
    a = cli(__doc__)
    d = load(a.datadir)
    n = len(d["spine_scoping"])

    banner(f"PLIDA-SIM modules at {a.datadir}")
    rows = []
    for m in MODULES:
        df = d[m]
        has_person = "person_id" in df.columns
        has_year = "ref_year" in df.columns
        grain = ("person × year" if has_person and has_year
                 else "person" if has_person else "year")
        rows.append({
            "module": m,
            "grain": grain,
            "rows": len(df),
            "persons": df["person_id"].nunique() if has_person else "—",
            "coverage": f"{100 * df['person_id'].nunique() / n:.1f}%" if has_person else "—",
            "columns": df.shape[1],
        })
    print(pd.DataFrame(rows).to_string(index=False))

    banner("Grain check: is each module one row per person per year?")
    for m in MODULES:
        df = d[m]
        if "person_id" not in df.columns:
            continue
        keys = ["person_id"] + (["ref_year"] if "ref_year" in df.columns else [])
        dupes = len(df) - len(df.drop_duplicates(keys))
        verdict = "one row per key" if dupes == 0 else f"{dupes:,} extra rows — MUST AGGREGATE"
        print(f"  {m:22s} {verdict}")

    banner("What an absent row means (Table 2.3)")
    print("  pit_income        did not lodge a return          -> MNAR, see 2.7")
    print("  domino_payments   no payment of that type         -> zero")
    print("  mbs_pbs_health    no service contact              -> zero")
    print("  census16_person   Census non-response             -> MAR, see 2.7")
    print("  after last_active_year                            -> attrition, see 2.8")

if __name__ == "__main__":
    main()
