#!/usr/bin/env python3
"""
Appendices A and B, generated from the data and from the chapters
=================================================================
Appendix A, the PLIDA-SIM data dictionary, is built from the dataset's own
manifest and from the values in the files, with a one-line description of each
column held below. Appendix B, the script index, is built from the script
tables at the end of each chapter. Neither is written by hand, so neither can
drift from what it describes: audit.py regenerates both and fails if the
committed copies differ.

    python appendices/make_appendices.py              # writes manuscript/appA_ and appB_content.js
    python appendices/make_appendices.py --check      # exit 1 if either is out of date
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "plida_sim" / "plida_sim_a"
MS = REPO / "manuscript"

MODULES = {   # file: (what it is, grain)
    "spine_scoping": ("Person spine: who is in scope in each year", "Person"),
    "core_demographics": ("Core demographics", "Person"),
    "core_locations": ("Location in each year", "Person-year"),
    "census16_person": ("2016 Census", "Person, Census respondents only"),
    "pit_income": ("Personal income tax", "Person-year, lodgers only"),
    "domino_payments": ("Income support payments (DOMINO)", "Person-year-payment type"),
    "mbs_pbs_health": ("Medicare and PBS health services", "Person-year, users only"),
    "epp_program": ("Employment Pathways Programme extract", "Participant"),
    "reference_indices": ("Price and wage indices", "Year"),
}

DESCRIBE = {
    "person_id": "Person identifier on the spine; present in every module",
    "in_scope_2014": "In scope of the population in the year (1) or not (0); likewise for 2015 to 2019",
    "deceased_year": "Year of death, if before 2020",
    "emigrated_year": "Year of emigration, if before 2020",
    "last_active_year": "Last year with any administrative activity",
    "birth_year": "Year of birth",
    "sex": "Sex",
    "country_of_birth_group": "Australia, main English-speaking countries (MESC) or other",
    "year_of_arrival": "Year of arrival in Australia; blank for the Australian-born",
    "ref_year": "Reference year of the record",
    "state": "State or territory of usual residence",
    "remoteness_area": "Remoteness area of usual residence",
    "sa4_code": "Statistical Area Level 4 of usual residence",
    "seifa_irsd_decile": "Decile of the Index of Relative Socio-economic Disadvantage (1 most disadvantaged)",
    "highest_edu": "Highest level of education",
    "labour_force_status_2016": "Labour force status at the 2016 Census",
    "english_proficiency": "Proficiency in spoken English",
    "dependent_children": "Number of dependent children (3 means three or more)",
    "family_composition": "Family composition",
    "salary_wages_nominal": "Salary and wages for the year, nominal dollars",
    "total_income_nominal": "Total income for the year, nominal dollars",
    "occupation_group": "Occupation, ANZSCO major group",
    "payment_type": "Type of income support payment",
    "fortnights_on_payment": "Fortnights on this payment type in the year",
    "payment_amount_nominal": "Amount paid on this payment type in the year, nominal dollars",
    "mutual_obligation_status": "Activity requirement attached to the payment (the near-instrument)",
    "gp_attendances": "General practitioner attendances in the year",
    "mh_item_flag": "Any mental health Medicare item in the year (1) or none (0)",
    "pbs_scripts": "PBS prescriptions dispensed in the year",
    "commencement_date": "Date of commencement in the programme, 2017",
    "referral_type": "Voluntary or mandatory referral; exists only for participants (post-treatment)",
    "service_stream": "Service stream allocated at commencement",
    "weeks_in_program": "Weeks in the programme",
    "cpi_index": "Consumer Price Index, 2019 = 100",
    "wpi_index": "Wage Price Index, 2019 = 100",
}

ANALYSIS = {   # the columns Chapter 2 constructs, beyond those carried from the modules
    "fortnights": "Fortnights on income support in 2016, summed across payment types",
    "treated": "Commenced the programme in 2017 (1) or not (0)",
    "eligible": "Aged 22 to 59 in 2016, on income support in 2015 or 2016 and in scope in 2016",
    "payment_amount_real": "Income support paid in 2016, constant 2019 dollars",
    "earnings_2014": "Salary and wages, constant 2019 dollars; likewise earnings_2015 to earnings_2019",
    "earnings_drop_2016": "Proportional fall in earnings from 2015 to 2016",
    "earnings_volatility": "Coefficient of variation of earnings, 2014 to 2016",
    "age_2016": "Age in 2016",
}

TRUTH = {
    "true_propensity": "True probability of taking part, from the generator's assignment equation",
    "y0": "Potential 2019 earnings without the programme, constant 2019 dollars",
    "y1": "Potential 2019 earnings after the programme, constant 2019 dollars",
    "tau_i": "The person's true effect, y1 − y0",
    "treated": "Took part (1) or not (0)",
    "earnings_shock_2016": "Pre-programme earnings shock (1) or not (0); in no analysis module",
    "u_employability": "Latent employability; in no analysis module",
    "attrited": "Left the data before 2019 (1) or not (0)",
    "attrition_reason": "Deceased, emigrated or out of scope",
}


def values(s: pd.Series) -> str:
    """A short statement of the values a column takes, read from the data."""
    plain = "year" in s.name or s.name.endswith("_code")      # no thousands separator
    s = s.dropna()
    if s.empty:
        return ""
    if s.dtype == object:
        u = sorted(s.unique())
        return "; ".join(u) if len(u) <= 8 else f"{len(u):,} values"
    u = s.nunique()
    if u <= 2:
        return " or ".join(str(int(x)) for x in sorted(s.unique()))
    lo, hi = s.min(), s.max()
    if float(lo).is_integer() and float(hi).is_integer():
        return f"{int(lo)} to {int(hi)}" if plain else f"{int(lo):,} to {int(hi):,}"
    return "continuous"


def row(*cells):
    return "    " + json.dumps(list(cells), ensure_ascii=False) + ","


def appendix_a() -> str:
    m = json.loads((DATA / "manifest.json").read_text())
    out = ["// Appendix A. Generated by appendices/make_appendices.py; do not edit by hand.", "",
           "module.exports = [", "",
           '["h1", "Appendix A  The PLIDA-SIM data dictionary"],', ""]
    out.append('["p", ' + json.dumps(
        f"This appendix describes PLIDA-SIM version {m['dataset_version']}, the dataset used throughout "
        f"the book. It holds {m['n_persons']:,} simulated persons observed from {m['years'][0]} to "
        f"{m['years'][-1]}; the programme commenced in {m['treatment_year']} and the outcome is earnings in "
        f"{m['outcome_year']}. Monetary amounts in the modules are nominal, and the indices in "
        f"reference_indices.csv, with {m['index_base_year']} = 100, convert them to constant dollars "
        "(Section 2.6.5). Table A.1 lists the nine modules, Table A.2 their columns, Table A.3 the columns "
        "that Chapter 2 constructs in the analysis file, and Table A.4 the truth file, which is used only "
        "to score results. The values shown are those of the primary dataset (seed "
        f"{m['seed']}); PLIDA-SIM B has the same structure. No record in PLIDA-SIM describes a real "
        "person.", ensure_ascii=False) + "],")
    out += ["", '["tab", "A.1", "The nine PLIDA-SIM modules.",', "  [2600, 3200, 2226, 1000],",
            '  ["File", "Content", "Grain", "Rows"],', "  ["]
    for f, (what, grain) in MODULES.items():
        out.append(row(f + ".csv", what, grain, f"{m['files'][f]['rows']:,}"))
    out += ["  ],", '  "Rows are for the primary dataset. Section 2.5.1 explains what an absent row means in each module.",',
            '  ["l", "l", "l", "r"]', "],", ""]
    out += ['["tab", "A.2", "The columns of the modules.",', "  [2000, 2300, 2400, 2326],",
            '  ["File", "Column", "Values", "Description"],', "  ["]
    seen = set()
    for f in MODULES:
        d = pd.read_csv(DATA / f"{f}.csv")
        for c in m["files"][f]["columns"]:
            if c == "person_id" and "person_id" in seen:
                continue
            if re.fullmatch(r"in_scope_201[5-9]", c):
                continue
            seen.add(c)
            out.append(row(f, c, values(d[c]), DESCRIBE[c]))
    out += ["  ],", '  "person_id is listed once; in_scope_2015 to in_scope_2019 follow in_scope_2014.",',
            '  ["l", "l", "l", "l"]', "],", ""]
    a = pd.read_csv(DATA / "analysis_file.csv")
    out += ['["tab", "A.3", "The columns Chapter 2 constructs in the analysis file.",', "  [2200, 2400, 4426],",
            '  ["Column", "Values", "Description"],', "  ["]
    for c, desc in ANALYSIS.items():
        out.append(row(c, values(a[c]), desc))
    out += ["  ],", '  ' + json.dumps(
        f"The analysis file has {a.shape[0]:,} rows, one per person, and {a.shape[1]} columns; the others are "
        "carried from the modules for 2016, as Table A.2 describes. Built by Scripts 2.5 and 2.6.") + ",",
            '  ["l", "l", "l"]', "],", ""]
    t = pd.read_csv(DATA / "truth" / "truth_parameters.csv")
    out += ['["tab", "A.4", "The truth file, truth/truth_parameters.csv.",', "  [2400, 2200, 4426],",
            '  ["Column", "Values", "Description"],', "  ["]
    for c, desc in TRUTH.items():
        out.append(row(c, values(t[c]), desc))
    out += ["  ],", '  "One row per person. The truth file of PLIDA-SIM B is withheld from readers; see Section 1.5.2.",',
            '  ["l", "l", "l"]', "],", "", "];", ""]
    return "\n".join(out)


def appendix_b() -> str:
    out = ["// Appendix B. Generated by appendices/make_appendices.py; do not edit by hand.", "",
           "module.exports = [", "", '["h1", "Appendix B  Script index"],', "",
           '["p", "Table B.1 lists every script in the companion repository with the exhibits it produces, in '
           'the order in which the scripts should be run within each chapter. Every chapter except Chapter 2 '
           'starts from the analysis file that Scripts 2.5 and 2.6 write, so those two must be run first. '
           'The table is compiled from the script tables at the end of each chapter, and the audit script '
           'checks that the two agree."],', "",
           '["tab", "B.1", "The scripts, by chapter.",', "  [900, 3900, 3200, 1026],",
           '  ["Script", "File", "Produces", "Runtime"],', "  ["]
    for ms in sorted(MS.glob("ch[01][0-9]_content.js")):
        txt = ms.read_text()
        tabs = [x.start() for x in re.finditer(r'\["tab", "\d{1,2}\.\d+"', txt)]
        block = txt[tabs[-1]:txt.find("\n],\n", tabs[-1])]
        for r in re.findall(r'^\s*(\["\d{1,2}\.\d+", "ch[01]\d/[^"]+\.py", "(?:[^"\\]|\\.)*", "(?:[^"\\]|\\.)*"\])',
                            block, re.M):
            out.append("    " + json.dumps(json.loads(r), ensure_ascii=False) + ",")
    out += ["  ],", '  "Runtimes are for an ordinary laptop. Scripts that repeat an experiment across draws accept '
            '--quick for a single draw.",', '  ["l", "l", "l", "r"]', "],", "", "];", ""]
    return "\n".join(out)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    a = p.parse_args()
    want = {MS / "appA_content.js": appendix_a(), MS / "appB_content.js": appendix_b()}
    stale = [f.name for f, t in want.items() if not f.exists() or f.read_text() != t]
    if a.check:
        print("stale: " + ", ".join(stale) if stale else "appendices current")
        return 1 if stale else 0
    for f, t in want.items():
        f.write_text(t)
        print(f"wrote {f.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
