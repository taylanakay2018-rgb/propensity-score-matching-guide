#!/usr/bin/env python3
"""
Project audit — book design, data, code and manuscript
=======================================================

One harness covering everything that can be checked mechanically, so that a
change anywhere is caught before it reaches a reader.

    python audit.py --repo psm-book --manuscript ../ch02_content.js
    python audit.py --strict          # non-zero exit on any FAIL

Run once per chapter manuscript. Chapter 5 additionally reads the results
files Script 5.3 writes (figures/matching_results.csv and
figures/matching_mahalanobis.csv), so run that script first:

    python ch05/05_03_compare_variants.py
    python audit.py --repo . --manuscript manuscript/ch05_content.js --strict

Five layers:

  A  Repository integrity   files, imports, syntax, CLI contracts, pinning
  B  Data contract          schema, grain, referential integrity, ranges
  C  Engineered pathologies the deliberate faults are present at spec size
  D  Statistical benchmarks the numbers the book quotes are reproducible
  E  Manuscript consistency every claim, cross-reference and citation resolves

Layer E is the one that matters most and is the least standard. Every number
quoted in the chapter is re-derived from the data and compared; every
"Section 2.x" reference is checked against the actual headings; every script
and figure filename cited is checked to exist. From Chapter 5 onwards every
cell of every results table is parsed out of the manuscript and compared with
the data at the precision it is printed to.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

RESULTS: list[tuple[str, str, str, str]] = []   # layer, check, status, detail


def record(layer: str, check: str, ok: bool | None, detail: str = "") -> bool:
    status = "INFO" if ok is None else ("PASS" if ok else "FAIL")
    RESULTS.append((layer, check, status, detail))
    return bool(ok)


def close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol


# ===========================================================================
# A. Repository integrity
# ===========================================================================

REQUIRED = [
    "make_data.py", "validate_data.py", "stability.py", "forward_dependencies.py",
    "requirements.txt", "environment.yml", "colab/make_notebooks.py",
    "README.md", "LICENCE", ".gitignore", ".github/workflows/ci.yml",
    "ch02/_common.py", "ch03/_common3.py",
    *[f"ch02/02_0{i}_{n}.py" for i, n in enumerate(
        ["load_modules", "coverage_and_units", "plida_sim_properties",
         "covariate_sets", "link_modules", "reshape_panel",
         "missingness_experiment", "attrition", "score_against_truth"], start=1)],
    *[f"ch03/03_0{i}_{n}.py" for i, n in enumerate(
        ["covariate_sets", "estimate_logit", "estimate_gbm", "compare_estimators",
         "specifications", "diagnose_score", "near_instrument"], start=1)],
    "ch04/_common4.py",
    *[f"ch04/04_0{i}_{n}.py" for i, n in enumerate(
        ["assess_overlap", "trimming_rules", "compare_rules", "who_is_removed"],
        start=1)],
    "ch05/_common5.py",
    *[f"ch05/05_0{i}_{n}.py" for i, n in enumerate(
        ["match_basics", "match_variants", "compare_variants",
         "reuse_and_balance"], start=1)],
    "ch06/_common6.py",
    *[f"ch06/06_0{i}_{n}.py" for i, n in enumerate(
        ["build_weights", "compare_weighting", "right_for_the_wrong_reason"], start=1)],
    "ch07/_common7.py",
    "ch08/_common8.py",
    "ch09/_common9.py",
    *[f"ch09/09_0{i}_{n}.py" for i, n in enumerate(
        ["estimate_primary", "standard_errors_across_draws"], start=1)],
    "results/ch09_standard_errors_200.csv",
    *[f"ch08/08_0{i}_{n}.py" for i, n in enumerate(
        ["balance_table", "diagnostics_across_draws"], start=1)],
    *[f"ch07/07_0{i}_{n}.py" for i, n in enumerate(
        ["form_strata", "compare_strata", "spline_on_score"], start=1)],
    "ch01/01_01_overview.py", "appendices/make_appendices.py",
    "ch10/_common10.py",
    *[f"ch10/10_0{i}_{n}.py" for i, n in enumerate(
        ["sources_of_bias", "sensitivity"], start=1)],
]


def layer_a(repo: Path) -> None:
    L = "A repo"
    for rel in REQUIRED:
        record(L, f"exists: {rel}", (repo / rel).exists())

    pys = sorted(repo.rglob("*.py"))
    record(L, "python files found", len(pys) >= 12, f"{len(pys)} files")

    for f in pys:
        rel = f.relative_to(repo)
        src = f.read_text()
        try:
            tree = ast.parse(src)
            record(L, f"compiles: {rel}", True)
        except SyntaxError as e:
            record(L, f"compiles: {rel}", False, str(e))
            continue
        record(L, f"has docstring: {rel}", ast.get_docstring(tree) is not None)
        # absolute paths that would only work on the author's machine
        bad = re.findall(r'["\'](/(?:home|Users|sessions|tmp)/[^"\']*)["\']', src)
        record(L, f"no absolute paths: {rel}", not bad, ", ".join(bad[:2]))

    # requirements pin every package
    reqs = [l.strip() for l in (repo / "requirements.txt").read_text().splitlines()
            if l.strip() and not l.startswith("#")]
    unpinned = [r for r in reqs if "==" not in r]
    record(L, "every requirement pinned", not unpinned, ", ".join(unpinned))

    # -- environment.yml carries the same pins as requirements.txt -----------
    # The README offers both routes. Two files that pin the same packages drift
    # unless something holds them together.
    def pins(text, sep):
        return {m.group(1).lower(): m.group(2) for m in
                re.finditer(rf"^[\s-]*([A-Za-z0-9_.-]+)\s*{sep}\s*([\w.]+)\s*$", text, re.M)}
    req_pins = pins((repo / "requirements.txt").read_text(), "==")
    env_txt = (repo / "environment.yml").read_text() if (repo / "environment.yml").exists() else ""
    env_pins = {**pins(env_txt, "="), **pins(env_txt, "==")}
    env_pins.pop("python", None)
    for pkg, ver in sorted(req_pins.items()):
        record(L, f"environment.yml pins {pkg} as requirements.txt does",
               env_pins.get(pkg) == ver, f"requirements {ver} · environment {env_pins.get(pkg)}")
    extra = sorted(set(env_pins) - set(req_pins))
    record(L, "environment.yml pins nothing requirements.txt does not", not extra, ", ".join(extra))

    # CI references only files that exist
    ci = (repo / ".github/workflows/ci.yml").read_text()
    for ref in re.findall(r"python (\S+\.py)", ci):
        if "$" not in ref and "*" not in ref:
            record(L, f"CI target exists: {ref}", (repo / ref).exists())

    # -- each figure has exactly one producer ------------------------------
    # Until v4.7, Figure 2.2 was written both by Script 2.7, which Table 2.10
    # credits, and by a root-level ch02_figures.py that redrew hard-coded
    # copies of Script 2.7's numbers on a different axis. Whichever ran last
    # decided what a reader saw.
    writers: dict[str, list[str]] = {}
    for f in pys:
        if f.name == "audit.py":
            continue
        for stem in set(re.findall(r"figure_\d_\d_[a-z_]+[a-z]", f.read_text())):
            writers.setdefault(stem, []).append(str(f.relative_to(repo)))
    for stem, who in sorted(writers.items()):
        record(L, f"one producer: {stem}", len(who) == 1, ", ".join(sorted(who)))

    # -- the README agrees with each chapter's script table ----------------
    # The v1.1.0 README credited six of the nine Chapter 2 scripts with the
    # wrong tables, from a numbering the chapter had long since left.
    readme = (repo / "README.md").read_text()
    # A fence carrying a language tag can only open a block. The v1.1.0 README
    # opened a second ```bash block inside an unclosed first one, which renders
    # the rest of "Start here" as code while the fence count stays even.
    inside, bad = False, []
    for k, ln in enumerate(readme.splitlines(), 1):
        if ln.startswith("```"):
            if inside and ln.strip() != "```":
                bad.append(k)
            else:
                inside = not inside
    record(L, "README code fences are well formed", not bad and not inside,
           f"block opened inside a block at line(s) {bad}" if bad else
           ("unclosed block at end" if inside else ""))
    mss = sorted((repo / "manuscript").glob("ch[01][0-9]_content.js"))
    for ms in mss:
        txt = ms.read_text()
        tabs = [m.start() for m in re.finditer(r'\["tab", "\d{1,2}\.\d+"', txt)]
        block = txt[tabs[-1]:txt.find("\n],\n", tabs[-1])] if tabs else ""
        for row in re.findall(r'^\s*(\["\d{1,2}\.\d+", "ch[01]\d/[^"]+\.py", "(?:[^"\\]|\\.)*", "(?:[^"\\]|\\.)*"\])',
                              block, re.M):
            n, f_, prod, rt = json.loads(row)
            line = f"| {n} | `{f_}` | {prod} | {rt} |"
            record(L, f"README lists Script {n} as the chapter does", line in readme,
                   "" if line in readme else f"expected: {line}")

    # -- one Colab notebook per chapter, current with the README -------------
    # The notebooks are generated from the README's chapter tables, which the
    # checks above hold to the manuscripts. Rebuilding them here means a
    # chapter cannot gain a script its notebook does not run.
    sys.path.insert(0, str(repo / "colab"))
    try:
        import make_notebooks as mnb
        want = mnb.build(readme)
        repo_addr = mnb.current_repo(readme)
        for d in sorted(p_.name for p_ in repo.glob("ch[01][0-9]") if p_.is_dir()):
            rel = f"colab/{d}.ipynb"
            have = (repo / rel).read_text() if (repo / rel).exists() else None
            record(L, f"Colab notebook current: {rel}", have is not None and have == want.get(rel),
                   "missing" if have is None else
                   ("" if have == want.get(rel) else "run python colab/make_notebooks.py"))
            if have:
                nb = json.loads(have)
                run = [ln[len("!python "):].split()[0] for c in nb["cells"] if c["cell_type"] == "code"
                       for ln in c["source"].splitlines() if ln.startswith(f"!python {d}/")]
                on_disk = sorted(str(f.relative_to(repo)) for f in (repo / d).glob(f"{d[2:]}_*.py"))
                record(L, f"{rel} runs every {d} script, in order", run == on_disk,
                       f"runs {len(run)} · on disk {len(on_disk)}")
            record(L, f"README has the Colab badge for {d}",
                   mnb.badge(d[2:], repo_addr) in readme)
        record(L, "Colab repository address set", None if repo_addr == mnb.PLACEHOLDER else True,
               f"still the placeholder {repo_addr}; run python colab/make_notebooks.py --repo OWNER/NAME"
               if repo_addr == mnb.PLACEHOLDER else repo_addr)
    finally:
        sys.path.pop(0)

    # -- the appendices are generated, and must be current -----------------
    # Appendix A is built from the data and Appendix B from the chapters'
    # script tables, so a chapter cannot gain a script the index omits.
    if (repo / "plida_sim" / "plida_sim_a" / "manifest.json").exists():
        r_ = subprocess.run([sys.executable, str(repo / "appendices" / "make_appendices.py"), "--check"],
                            capture_output=True, text=True)
        record(L, "Appendices A and B current", r_.returncode == 0,
               r_.stdout.strip() or "run python appendices/make_appendices.py")

    # -- CI runs every chapter, both harnesses, and audits every manuscript --
    ci_txt = (repo / ".github/workflows/ci.yml").read_text()
    for d in sorted(p_.name for p_ in repo.glob("ch[01][0-9]") if p_.is_dir()):
        record(L, f"CI runs {d}/", f"{d}/" in ci_txt)
    record(L, "CI runs stability.py", "python stability.py" in ci_txt)
    # -- scripts that generate draws clean up after themselves --------------
    # Until v5.1 every multi-draw script left its draws in the system temporary
    # folder, about 150 MB each: a full run of the book's scripts left several
    # gigabytes behind on a reader's machine.
    for f in pys:
        src = f.read_text()
        if "mkdtemp(" in src and f.name != "audit.py":
            record(L, f"removes its temporary draws: {f.relative_to(repo)}",
                   "atexit.register(shutil.rmtree" in src)
    record(L, "CI builds environment.yml", "environment-file: environment.yml" in ci_txt)
    record(L, "CI runs forward_dependencies.py --strict",
           bool(re.search(r"python forward_dependencies\.py .*--strict", ci_txt)))
    loop = re.search(r"for c in ([\d ]+); do\s+.*?audit\.py", ci_txt, re.S)
    audited = set(loop.group(1).split()) if loop else set()
    have_ms = {str(int(re.search(r"ch(\d\d)_", m.name).group(1))) for m in mss}
    record(L, "CI audits every chapter manuscript", have_ms <= audited,
           f"manuscripts {sorted(have_ms)} · audited {sorted(audited)}")

    # every chapter script accepts --datadir or documents why not
    for f in sorted(list((repo / "ch01").glob("01_*.py"))
                    + list((repo / "ch02").glob("02_*.py"))
                    + list((repo / "ch03").glob("03_*.py"))
                    + list((repo / "ch04").glob("04_*.py"))
                    + list((repo / "ch05").glob("05_*.py"))
                    + list((repo / "ch06").glob("06_*.py"))
                    + list((repo / "ch07").glob("07_*.py"))
                    + list((repo / "ch08").glob("08_*.py"))
                    + list((repo / "ch09").glob("09_*.py"))
                    + list((repo / "ch10").glob("10_*.py"))):
        src = f.read_text()
        record(L, f"CLI contract: {f.name}",
               "cli(" in src or "argparse" in src, "no argument parsing")


# ===========================================================================
# B. Data contract
# ===========================================================================

GRAIN = {
    "spine_scoping": ["person_id"],
    "core_demographics": ["person_id"],
    "core_locations": ["person_id", "ref_year"],
    "census16_person": ["person_id"],
    "pit_income": ["person_id", "ref_year"],
    "domino_payments": ["person_id", "ref_year", "payment_type"],
    "mbs_pbs_health": ["person_id", "ref_year"],
    "epp_program": ["person_id"],
    "reference_indices": ["ref_year"],
}
CATEGORIES = {
    ("core_demographics", "sex"): {"Male", "Female"},
    ("core_demographics", "country_of_birth_group"): {"Australia", "MESC", "Other"},
    ("core_locations", "remoteness_area"): {"Major Cities", "Inner Regional",
                                            "Outer Regional", "Remote+"},
    ("census16_person", "highest_edu"): {"<Year 12", "Year 12", "Cert III/IV",
                                         "Diploma", "Bachelor+"},
    ("census16_person", "english_proficiency"): {"Well", "Not well"},
    ("epp_program", "referral_type"): {"Voluntary", "Mandatory"},
    ("domino_payments", "mutual_obligation_status"): {"Exempt", "Partial", "Full",
                                                      "Intensive"},
}


def layer_b(data: Path) -> dict:
    L = "B data"
    d = {}
    for m in GRAIN:
        p = data / f"{m}.csv"
        if not p.exists():
            record(L, f"module present: {m}", False)
            continue
        d[m] = pd.read_csv(p)
        record(L, f"module present: {m}", True, f"{len(d[m]):,} rows")

    spine = set(d["spine_scoping"].person_id)
    record(L, "spine size", len(spine) == 50_000, f"{len(spine):,}")
    record(L, "person_id format",
           bool(re.fullmatch(r"PLIDASIM_\d{6}", d["spine_scoping"].person_id.iloc[0])))

    for m, keys in GRAIN.items():
        if m not in d:
            continue
        dupes = len(d[m]) - len(d[m].drop_duplicates(keys))
        record(L, f"grain unique: {m} on {'+'.join(keys)}", dupes == 0,
               f"{dupes:,} duplicate keys" if dupes else "")
        if "person_id" in d[m].columns:
            orphans = set(d[m].person_id) - spine
            record(L, f"referential integrity: {m}", not orphans,
                   f"{len(orphans):,} ids not in spine")

    for (m, col), allowed in CATEGORIES.items():
        if m in d and col in d[m].columns:
            seen = set(d[m][col].dropna().unique())
            record(L, f"category domain: {m}.{col}", seen <= allowed,
                   f"unexpected {sorted(seen - allowed)}")

    # ranges
    age = 2016 - d["core_demographics"].birth_year
    record(L, "age within 22-59 at baseline", bool(age.between(22, 59).all()),
           f"{age.min()}-{age.max()}")
    record(L, "SEIFA decile 1-10",
           bool(d["core_locations"].seifa_irsd_decile.between(1, 10).all()))
    record(L, "fortnights 0-26",
           bool(d["domino_payments"].fortnights_on_payment.between(0, 26).all()))
    money = [c for m in d for c in d[m].columns if c.endswith("_nominal")]
    record(L, "no negative money",
           all((d[m][c] >= 0).all() for m in d for c in d[m].columns
               if c.endswith("_nominal")), f"{len(money)} money columns")
    ri = d["reference_indices"]
    record(L, "index base year is 100",
           close(float(ri.loc[ri.ref_year == 2019, "cpi_index"].iloc[0]), 100.0, 0.01))
    record(L, "six index rows", len(ri) == 6)

    # truth is isolated and does not leak
    tp = data / "truth" / "truth_parameters.csv"
    record(L, "truth file quarantined in truth/", tp.exists())
    leak = [c for m in d for c in d[m].columns
            if c in {"y0", "y1", "tau_i", "true_propensity", "earnings_shock_2016"}]
    record(L, "no truth columns in analysis modules", not leak, ", ".join(leak))

    man = data / "manifest.json"
    record(L, "manifest present", man.exists())
    if man.exists():
        mj = json.loads(man.read_text())
        record(L, "manifest row counts agree",
               all(mj["files"][m]["rows"] == len(d[m]) for m in d if m in mj["files"]))
    return d


def layer_b_reproducibility(repo: Path, tmp: Path) -> None:
    L = "B data"
    a1, a2 = tmp / "det1", tmp / "det2"
    for out in (a1, a2):
        subprocess.run([sys.executable, str(repo / "make_data.py"),
                        "--n", "4000", "--outdir", str(out), "--quiet"], check=True)
    same = all((a1 / f.name).read_bytes() == f.read_bytes()
               for f in a2.glob("*.csv"))
    record(L, "byte-identical across runs", same)

    b = tmp / "variantb"
    subprocess.run([sys.executable, str(repo / "make_data.py"), "--variant", "B",
                    "--n", "4000", "--outdir", str(b), "--quiet"], check=True)
    same_schema = (pd.read_csv(a1 / "core_demographics.csv").columns.tolist()
                   == pd.read_csv(b / "core_demographics.csv").columns.tolist())
    differs = not (pd.read_csv(a1 / "core_demographics.csv").birth_year
                   .equals(pd.read_csv(b / "core_demographics.csv").birth_year))
    record(L, "variant B same schema", same_schema)
    record(L, "variant B different values", differs)

    nt = tmp / "notruth"
    subprocess.run([sys.executable, str(repo / "make_data.py"), "--n", "1000",
                    "--no-truth", "--outdir", str(nt), "--quiet"], check=True)
    record(L, "--no-truth withholds the truth file",
           not (nt / "truth" / "truth_parameters.csv").exists())
    # A reader who goes looking should find an explanation, not an empty
    # folder and not a README describing a file that is not there.
    note = nt / "truth" / "README.md"
    record(L, "--no-truth explains the withholding",
           note.exists() and "Withheld deliberately" in note.read_text())


# ===========================================================================
# C. Engineered pathologies
# ===========================================================================

def layer_c(d: dict, data: Path) -> None:
    L = "C faults"
    n = 50_000
    t = pd.read_csv(data / "truth" / "truth_parameters.csv").set_index("person_id")
    D = t.treated.values == 1

    cen = 100 * (1 - len(d["census16_person"]) / n)
    record(L, "Census non-response ~7.2%", close(cen, 7.2, 2.0), f"{cen:.2f}%")

    pit16 = d["pit_income"].query("ref_year == 2016")
    nl = 100 * (1 - len(pit16) / n)
    record(L, "PIT non-lodgers 2016 ~10.9%", close(nl, 10.9, 3.0), f"{nl:.2f}%")

    hl = d["mbs_pbs_health"]
    absent = 100 * (1 - len(hl) / (n * 6))
    record(L, "health structural absence",
           close(absent, 19.5, 4.0), f"{absent:.1f}%")

    sp = d["spine_scoping"].set_index("person_id").reindex(t.index)
    left = (sp.last_active_year < 2019).values
    record(L, "attrition ~12.5%", close(100 * left.mean(), 12.5, 2.5),
           f"{100*left.mean():.2f}%")
    diff = 100 * (left[D].mean() - left[~D].mean())
    record(L, "attrition differential positive", diff > 2.0, f"{diff:+.2f} pp")
    lab = 100 * (sp.deceased_year.notna() | sp.emigrated_year.notna()).mean()
    record(L, "unlabelled route is the largest",
           (100 * left.mean() - lab) > lab, f"labelled {lab:.1f}% of {100*left.mean():.1f}%")

    # the post-treatment trap must in fact be a trap
    prog = set(d["epp_program"].person_id)
    trap = np.array([p in prog for p in t.index])
    record(L, "referral_type separates perfectly", bool((trap == D).all()))

    # deflation gap
    ri = d["reference_indices"].set_index("ref_year")
    gap = 100 - float(ri.loc[2016, "cpi_index"])
    record(L, "2016 deflation gap ~6%", close(gap, 6.0, 1.0), f"{gap:.2f}%")

    # MNAR signature: non-lodgers differ on observables
    have = t.index.isin(pit16.person_id)
    dom = d["domino_payments"].query("ref_year == 2016")
    fn = dom.groupby("person_id").fortnights_on_payment.sum().reindex(t.index).fillna(0).values
    pooled = np.sqrt((fn[~have].var() + fn[have].var()) / 2)
    smd = (fn[~have].mean() - fn[have].mean()) / pooled
    record(L, "MNAR signature on fortnights (SMD > 0.4)", smd > 0.4, f"{smd:+.3f}")


# ===========================================================================
# D. Statistical benchmarks
# ===========================================================================

def layer_d(repo: Path, data: Path) -> dict:
    L = "D stats"
    t = pd.read_csv(data / "truth" / "truth_parameters.csv").set_index("person_id")
    D = t.treated.values == 1
    y = np.where(D, t.y1, t.y0)
    vals = {
        "ATE": t.tau_i.mean(), "ATT": t.tau_i[D].mean(), "ATC": t.tau_i[~D].mean(),
        "naive": y[D].mean() - y[~D].mean(),
        "y_untreated": y[~D].mean(),
    }
    record(L, "true ATE ~$5,157", close(vals["ATE"], 5157, 700), f"${vals['ATE']:,.0f}")
    record(L, "true ATT ~$6,192", close(vals["ATT"], 6192, 800), f"${vals['ATT']:,.0f}")
    record(L, "ATT exceeds ATE", vals["ATT"] > vals["ATE"],
           f"by {100*(vals['ATT']/vals['ATE']-1):.1f}%")
    record(L, "naive comparison has the wrong sign",
           vals["naive"] < 0 < vals["ATT"], f"${vals['naive']:,.0f}")

    r = subprocess.run([sys.executable, str(repo / "validate_data.py"),
                        "--datadir", str(data), "--strict"],
                       capture_output=True, text=True)
    tail = [l for l in r.stdout.splitlines() if "passed" in l]
    record(L, "validate_data.py --strict", r.returncode == 0,
           tail[-1].strip() if tail else r.stdout[-120:])
    return vals


# ===========================================================================
# E. Manuscript consistency
# ===========================================================================

def layer_e(manuscript: Path, repo: Path, d: dict, data: Path, vals: dict,
            ch: str = "2") -> None:
    L = f"E chapter {ch}"
    if not manuscript.exists():
        record(L, "manuscript found", False, str(manuscript))
        return
    s = manuscript.read_text()
    record(L, "manuscript found", True, f"{len(s.split()):,} tokens")

    # -- numbering: sequential, no gaps, no duplicates ----------------------
    # Fragments are matched on the caption form only (`], "Fragment 2.n  `),
    # so that in-text references to a fragment are not mistaken for its label.
    for kind, pat in [("Figure", rf'\["fig", "{ch}\.(\d+)"'),
                      ("Table", rf'\["tab", "{ch}\.(\d+)"'),
                      ("Fragment", rf'\], "Fragment {ch}\.(\d+)')]:
        nums = [int(x) for x in re.findall(pat, s)]
        record(L, f"{kind} numbering sequential", nums == sorted(set(nums)) == nums,
               f"{nums}")

    # -- headings appear in the order their numbers claim -------------------
    # Caught 2.6.6 sitting before 2.6.5 in draft v2.0.
    order = [tuple(int(p) for p in h.split("."))
             for h in re.findall(r'\["h[23]", "(\d+(?:\.\d+)+)', s)]
    bad = [f"{'.'.join(map(str, b))} after {'.'.join(map(str, a))}"
           for a, b in zip(order, order[1:]) if b < a]
    record(L, "headings appear in numerical order", not bad, f"out of order: {bad}")

    # -- every fragment referenced in prose is defined ----------------------
    # Caught a reference to a non-existent Fragment 2.8 in draft v2.0.
    # Until v4.5 these two patterns were hard-wired to Chapter 2, so for
    # Chapters 3 and 4 the check compared two empty sets and always passed.
    frag_def = {int(x) for x in re.findall(rf'\], "Fragment {ch}\.(\d+)', s)}
    frag_ref = {int(x) for x in re.findall(rf"Fragment {ch}\.(\d+)", s)}
    record(L, "every Fragment reference is defined", frag_ref <= frag_def,
           f"undefined: {sorted(frag_ref - frag_def)}")

    # -- every heading referenced actually exists ---------------------------
    heads = set(re.findall(r'\["h[23]", "(\d{1,2}\.\d+(?:\.\d+)?)', s))
    # A chapter legitimately cites sections of other chapters. Resolve those
    # against the sibling manuscript when it is present, rather than calling
    # every forward and backward reference dangling.
    for sib in sorted(manuscript.parent.glob("ch[01][0-9]_content.js")):
        if sib != manuscript:
            heads |= set(re.findall(r'\["h[23]", "(\d{1,2}\.\d+(?:\.\d+)?)',
                                    sib.read_text()))
    refs = set(re.findall(r"(?<!\d)Section (\d{1,2}\.\d+(?:\.\d+)?)", s))
    missing = sorted(r for r in refs if r not in heads)
    record(L, "every Section cross-reference resolves", not missing,
           f"dangling: {missing}")

    # -- every Table/Figure referenced is defined ---------------------------
    defined_t = set(re.findall(r'\["tab", "(\d{1,2}\.\d+)"', s))
    for sib in sorted(manuscript.parent.glob("ch[01][0-9]_content.js")):
        if sib != manuscript:
            defined_t |= set(re.findall(r'\["tab", "(\d{1,2}\.\d+)"', sib.read_text()))
    used_t = set(re.findall(r"Table (\d{1,2}\.\d+)", s))
    record(L, "every Table reference is defined", used_t <= defined_t,
           f"undefined: {sorted(used_t - defined_t)}")
    defined_f = set(re.findall(r'\["fig", "(\d{1,2}\.\d+)"', s))
    for sib in sorted(manuscript.parent.glob("ch[01][0-9]_content.js")):
        if sib != manuscript:
            defined_f |= set(re.findall(r'\["fig", "(\d{1,2}\.\d+)"', sib.read_text()))
    used_f = set(re.findall(r"Figure (\d{1,2}\.\d+)", s))
    record(L, "every Figure reference is defined", used_f <= defined_f,
           f"undefined: {sorted(used_f - defined_f)}")

    # -- the scripts must cite the same exhibit numbers the chapter uses ----
    # Draft v3.0 had six wrong references here: Script 2.5 announced "Table 2.3"
    # while building Table 2.4, Script 2.8 announced "Table 2.7" for Table 2.8,
    # and so on. The manuscript checks above could not see any of it.
    chap_tab = {t for t, _ in re.findall(rf'\["tab", "({ch}\.\d+)", "([^"]{{0,60}})', s)}
    chap_frag = {f for f in re.findall(rf'\], "Fragment ({ch}\.\d+)', s)}
    cc = f"{int(ch):02d}"
    cdir = repo / f"ch{cc}"

    # Table 2.10 is the reader's map: which script produces which exhibit.
    # Parse it, then hold each script to what the table credits it with. The
    # weaker test -- does the cited table exist at all -- passes even when a
    # script announces the wrong one, which is exactly the defect that shipped
    # in draft v3.0.
    inv_num = max((t for t in chap_tab), key=lambda x: int(x.split(".")[1]), default=None)
    inv = re.search(rf'\["tab", "{re.escape(inv_num)}".*?\n\],\n', s, re.S) if inv_num else None
    credited: dict[str, set[str]] = {}
    if inv:
        for row in re.findall(rf'\["{ch}\.\d+", "ch{cc}/({cc}_\d\d_[a-z_]+\.py)", "([^"]*)"', inv.group(0)):
            got = set(re.findall(rf"{ch}\.\d+", row[1]))
            # "Tables 5.2 to 5.7" credits the four tables in between as well.
            for lo, hi in re.findall(rf"{ch}\.(\d+) to {ch}\.(\d+)", row[1]):
                got |= {f"{ch}.{k}" for k in range(int(lo), int(hi) + 1)}
            credited[row[0]] = got
        listed = set(credited)
        actual = {p.name for p in cdir.glob(f"{cc}_*.py")}
        record(L, f"Table {inv_num} lists every chapter script", listed == actual,
               f"only in table: {sorted(listed - actual)} · "
               f"only on disk: {sorted(actual - listed)}")
    else:
        record(L, "script inventory table parsed", False, "not found")

    for f in sorted(cdir.glob(f"{cc}_*.py")):
        src = f.read_text()
        bad_f = sorted({x for x in re.findall(rf"Fragment ({ch}\.\d+)", src)
                        if x not in chap_frag})
        record(L, f"{f.name} cites only real fragments", not bad_f,
               f"no such fragment: {bad_f}")
        # Tables the script announces as its own output. Only banner() counts:
        # a docstring may legitimately cross-reference a table produced
        # elsewhere, and that is not a claim about what this script emits.
        # f-strings count too: until v4.5 banner(f"Table 3.3 ...") was not
        # matched, so six scripts in Chapters 3 and 4 went unchecked here.
        banners = " ".join(re.findall(r'banner\(\s*f?"([^"]*)"', src))
        announced = set(re.findall(rf"Table ({ch}\.\d+)", banners))
        ghost = sorted(set(re.findall(rf"Table ({ch}\.\d+)", src)) - chap_tab)
        record(L, f"{f.name} cites only real tables", not ghost,
               f"no such table: {ghost}")
        if f.name in credited:
            wrong = sorted(announced - credited[f.name])
            record(L, f"{f.name} announces only tables the inventory credits it with",
                   not wrong,
                   f"announces {wrong}, credited with {sorted(credited[f.name])}")

    # -- every script and figure filename cited exists ----------------------
    for path in sorted(set(re.findall(rf"ch{cc}/{cc}_\d\d_[a-z_]+\.py", s))):
        record(L, f"cited script exists: {path}", (repo / path).exists())
    for fn in sorted(set(re.findall(rf"figure_{ch}_\d_[a-z_]+\.tif", s))):
        record(L, f"cited figure exists: {fn}", (repo / "figures" / fn).exists())

    # -- numeric claims, re-derived from the data ---------------------------
    # These are Chapter 2's claims. Until v4.5 they ran, and were reported as
    # "claim:" lines, whichever chapter was being audited.
    if ch == "2":
        layer_e2_claims(L, d, vals)

    # -- claims that must be present in the prose at all --------------------
    PHRASES = {
        "2": ["for the treated, against the untreated mean",
              "wrong sign", "69.8 per cent", "55.0 percentage points",
              "18.8 per cent", "cannot be distinguished from zero",
              "carried forward", "4.9 per cent low"],
        "3": ["balancing score", "prediction is not the objective",
              "effective control sample", "opposite signs",
              "consistently wrong", "0.000000"],
        "4": ["common support", "practical non-positivity",
              "the truth moving towards the estimate",
              "one rule, two estimands", "52.6 per cent", "$2,663"],
        "6": ["normalisation, not stabilisation", "do not cap the weights",
              "right for the wrong reason", "trimming the sample rather than capping",
              "pure outcome predictor"],
        "9": ["must reflect how the estimate was built", "everything the analyst did must be inside the loop",
              "measures sampling error", "the standard error of the difference",
              "never report the default standard error of a weighted regression"],
        "8": ["the balance that matters", "a threshold is a convention, not a test",
              "secondary check", "fitted to the controls only", "cross-fitted",
              "necessary condition", "not a sufficient condition"],
        "7": ["marginal mean weights through stratification", "overlap population",
              "right for the wrong reason, again", "evenly spaced knots",
              "regression within strata", "a second number of strata"],
        "1": ["selection bias", "balancing score", "selection on gains",
              "separation of design from analysis", "none of them can repair a failure of unconfoundedness",
              "the better score depends on how it is used"],
        "10": ["only one of them is unobservable", "describes assignment, not outcomes",
               "a complement to the specification checks", "rather than invent one",
               "the conclusion that matters to the decision",
               "with the specification checks of Section 10.2.1 already applied"],
        "5": ["pass all of them as well", "a secondary check that can tell the two apart",
              "the caliper does not matter", "the distance does matter",
              "noise mining", "nonparametric preprocessing",
              "necessary condition", "is not a sufficient one",
              "distinct controls alongside the number of pairs"],
    }
    for phrase in PHRASES.get(ch, []):
        record(L, f"prose retains: '{phrase}'", phrase.lower() in s.lower())
    # Until Chapter 5 v1.6, Section 5.15 promised that the diagnostics beyond the
    # mean "can distinguish these two samples"; Chapter 8 measured it, and they cannot.
    if ch == "5":
        record(L, "Section 5.15 no longer promises what Chapter 8 contradicts",
               "can distinguish these two samples where the standardised difference cannot" not in s)
    # Until Chapter 3 v1.3, Section 3.3 called the log transform "a much better
    # one" than dollars; Chapter 10 found that the dollar term also belongs.
    if ch == "3":
        record(L, "Section 3.3 no longer calls the log transform simply better",
               "much better one" not in s and "Section 10.2.1" in s)


def truth_values(data: Path) -> dict:
    """The three sets of true values the book uses (Section 1.5): all persons,
    the eligible population on the primary dataset, and the naive differences."""
    T = pd.read_csv(data / "truth" / "truth_parameters.csv").set_index("person_id")
    A = pd.read_csv(data / "analysis_file.csv").set_index("person_id")
    T = T.join(A[["eligible"]])
    t, e = T.treated == 1, T.eligible == 1
    y = pd.Series(np.where(t, T.y1, T.y0), index=T.index)   # as every chapter scores it
    return {"att_all": T.tau_i[t].mean(), "ate_all": T.tau_i.mean(),
            "att_elig": T.tau_i[t & e].mean(), "ate_elig": T.tau_i[e].mean(),
            "naive_elig": y[t & e].mean() - y[~t & e].mean(),
            "n_t_elig": int((t & e).sum()), "n_c_elig": int((~t & e).sum()),
            "n_elig": int(e.sum()), "att_obs": T.tau_i[t & (T.attrited == 0)].mean()}


def layer_e2_truth(s: str, data: Path) -> None:
    """Chapter 2 now names the eligible population's values beside its own."""
    L = "E chapter 2"
    v = truth_values(data)
    snip = "the ATT is $6,408, the ATE $5,412 and the raw difference −$2,910"
    record(L, "claim: eligible-population values $6,408, $5,412, −$2,910", snip in s
           and _agrees(v["att_elig"], "6,408") and _agrees(v["ate_elig"], "5,412")
           and _agrees(v["naive_elig"], "-2,910"),
           f"{v['att_elig']:,.0f} · {v['ate_elig']:,.0f} · {v['naive_elig']:,.0f}")
    record(L, "claim: $6,192 and $5,157 are over all 50,000 persons",
           "across all 50,000 persons and $5,895" in s and "averages over all 50,000 persons" in s
           and _agrees(v["att_all"], "6,192") and _agrees(v["ate_all"], "5,157")
           and _agrees(v["att_obs"], "5,895"), "")
    record(L, "Chapter 2 no longer calls the all-persons ATE the eligible one",
           "averages over everyone eligible" not in s and "across the full eligible population" not in s)


def layer_e1(s: str, repo: Path, data: Path, results: Path) -> None:
    L = "E chapter 1"
    prose = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)

    def claim(label, snippet, got, shown=None, ok=None):
        if snippet.lower() not in prose.lower():
            record(L, f"claim: {label}", False, f"text not found: '{snippet}'")
            return
        ok = _agrees(got, shown) if ok is None else ok
        record(L, f"claim: {label}", bool(ok), f"chapter {shown} · data {got:,.4f}" if shown else f"data {got:,.4f}")

    f = results / "overview_primary.csv"
    record(L, "Script 1.1 results present", f.exists(),
           "" if f.exists() else f"run ch01/01_01_overview.py first ({results})")
    if not f.exists():
        return
    v = pd.read_csv(f).set_index("quantity")["value"].to_dict()
    tv = truth_values(data)
    record(L, "Script 1.1 agrees with the audit's own true values",
           abs(v["att_elig"] - tv["att_elig"]) < 1e-6 and abs(v["naive_elig"] - tv["naive_elig"]) < 1e-6
           and abs(v["att_all"] - tv["att_all"]) < 1e-6)
    _, rows, cap = ms_table(s, "1.1")
    keys = {"All persons": "all", "Eligible population": "elig"}
    for r in rows:
        k = next(v_ for k_, v_ in keys.items() if r[0].startswith(k_))
        n = v["n_all"] if k == "all" else v["n_elig"]
        record(L, f"Table 1.1 {r[0]} · persons", _agrees(n, r[1]), f"chapter {r[1]} · data {n:,.0f}")
        for j, q in ((2, "att"), (3, "ate"), (4, "naive")):
            got = v[f"{q}_{k}"]
            record(L, f"Table 1.1 {r[0]} · {q}", _agrees(got, r[j].replace("$", "")),
                   f"chapter {r[j]} · data {got:,.1f}")
    pw = results / "weighting_results.csv"
    if pw.exists():
        w = pd.read_csv(pw)
        q = w[(w.score == "logit") & (w.trimmed == False)]
        ate6 = q[q.estimand == "ATE"].groupby("seed").truth.first().mean()
        att6 = q[q.estimand == "ATT"].groupby("seed").truth.first().mean()
        record(L, "Table 1.1 note: six-draw $6,446 and $5,417",
               "true ATT is $6,446 and its true ATE $5,417" in cap and _agrees(att6, "6,446")
               and _agrees(ate6, "5,417") and q.seed.nunique() == 6, f"{att6:,.0f} · {ate6:,.0f}")
    claim("4,867 of 42,575, 11.4 per cent", "4,867 of 42,575 persons took part, or 11.4 per cent",
          100 * v["n_t_elig"] / v["n_elig"], ok=v["n_t_elig"] == 4867 and v["n_elig"] == 42575
          and _agrees(100 * v["n_t_elig"] / v["n_elig"], "11.4"))
    claim("participants earned $2,910 less; truth $6,408", "the participants earned $2,910 less",
          v["naive_elig"], ok=_agrees(-v["naive_elig"], "2,910") and _agrees(v["att_elig"], "6,408")
          and "by $6,408 on average" in prose)
    claim("bias term about −$9,300", "the bias term is about −$9,300", v["naive_elig"] - v["att_elig"],
          ok=round(v["naive_elig"] - v["att_elig"], -2) == -9300)
    claim("ATT $6,408 exceeds ATE $5,412", "so that the ATT ($6,408) exceeds the ATE ($5,412)", v["ate_elig"],
          ok=_agrees(v["ate_elig"], "5,412") and v["att_elig"] > v["ate_elig"])
    e = lambda k: v[f"est_{k}"]                                               # noqa: E731
    b = lambda k: 100 * (v[f"est_{k}"] - v[f"truth_{k}"]) / v[f"truth_{k}"]  # noqa: E731
    claim("designs range $4,921 to $6,640", "from $4,921 for propensity score matching to $6,640 for Mahalanobis matching",
          e("match"), ok=_agrees(e("match"), "4,921") and _agrees(e("maha"), "6,640"))
    claim("odds weighting $5,601, 12.6 per cent low", "odds weighting gives $5,601, 12.6 per cent low", e("odds"),
          ok=_agrees(e("odds"), "5,601") and _agrees(-b("odds"), "12.6"))
    claim("recommended designs $6,193 and $6,209 within four per cent",
          "Mahalanobis matching with three controls gives $6,193, and odds weighting on the trimmed boosted score gives $6,209",
          e("maha13"), ok=_agrees(e("maha13"), "6,193") and _agrees(e("odds_gbm_trim"), "6,209")
          and abs(b("maha13")) < 4.5 and abs(b("odds_gbm_trim")) < 4.5)
    claim("outcome regression $6,294", "The outcome regression, at $6,294", e("regression"), "6,294")
    claim("naive in figure agrees", "The naive comparison is $2,910 below zero", e("naive"),
          ok=abs(e("naive") - v["naive_elig"]) < 1e-6)
    record(L, "Chapter 1 names the three assumptions",
           all(t in prose for t in ("unconfoundedness", "overlap", "stable unit treatment value assumption (SUTVA)")))


def layer_e2_claims(L: str, d: dict, vals: dict) -> None:
    n = 50_000
    pit16 = d["pit_income"].query("ref_year == 2016")
    dom16 = d["domino_payments"].query("ref_year == 2016")
    naive_merge = len(d["core_demographics"].merge(dom16, on="person_id", how="left"))
    inner = (d["core_demographics"][["person_id"]]
             .merge(pit16[["person_id"]], on="person_id")
             .merge(d["census16_person"][["person_id"]], on="person_id")
             .merge(d["mbs_pbs_health"].query("ref_year == 2016")[["person_id"]],
                    on="person_id"))
    prog = set(d["epp_program"].person_id)
    hl16 = d["mbs_pbs_health"].query("ref_year == 2016")
    gp_zero = hl16.gp_attendances.sum() / n
    age = 2016 - d["core_demographics"].set_index("person_id").birth_year
    on_sup = set(d["domino_payments"].query("ref_year in [2015, 2016]").person_id)
    in_sc = set(d["spine_scoping"].query("in_scope_2016 == 1").person_id)
    elig = set(age.index[age.between(22, 59)]) & on_sup & in_sc

    # v1.1.0 claims: the beta-binomial payment distribution, the occupation
    # carry-forward, and the complete-case deletion in Section 2.7.5.
    fn16 = (dom16.groupby("person_id").fortnights_on_payment.sum()
            .reindex(d["spine_scoping"].person_id).fillna(0))
    occ_ff = None
    for y in (2014, 2015, 2016):
        sy = (d["pit_income"].query("ref_year == @y").set_index("person_id")
              ["occupation_group"].dropna())
        occ_ff = sy if occ_ff is None else sy.combine_first(occ_ff)
    occ_none = n - occ_ff.reindex(d["spine_scoping"].person_id).notna().sum()
    cen = d["census16_person"].set_index("person_id")
    have = (set(pit16.dropna(subset=["salary_wages_nominal"]).person_id)
            & set(d["pit_income"].query("ref_year == 2015").person_id)
            & set(cen.dropna(subset=["highest_edu", "dependent_children",
                                     "english_proficiency"]).index))
    deleted = n - len(have)

    claims = [
        ("24.5 per cent on payment 20+ fortnights", 100 * (fn16 >= 20).mean(), 24.5, 2.0),
        ("6.95 per cent at the 26-fortnight cap", 100 * (fn16 == 26).mean(), 6.95, 1.2),
        ("172 with no occupation carried forward", int(occ_none), 172, 90),
        ("10,736 removed by listwise deletion", deleted, 10736, 700),
        ("53,033 rows", naive_merge, 53033, 900),
        ("3,033 duplicated persons",
         int((dom16.groupby("person_id").size() > 1).sum()), 3033, 600),
        ("34,900 people retained", len(inner), 34900, 700),
        ("10.74 per cent treated", 100 * len(prog) / n, 10.74, 0.8),
        ("9.99 per cent after inner join",
         100 * len(prog & set(inner.person_id)) / len(inner), 9.99, 0.9),
        ("7,753 with no health row", n - hl16.person_id.nunique(), 7753, 900),
        ("3.10 mean GP attendances", gp_zero, 3.10, 0.25),
        ("3.67 if absent dropped", hl16.gp_attendances.mean(), 3.67, 0.30),
        ("42,575 eligible", len(elig), 42575, 1200),
        ("502 participants outside eligibility", len(prog - elig), 502, 200),
        ("5,369 participants", len(prog), 5369, 350),
        ("$6,192 true ATT", vals["ATT"], 6192, 800),
        # Section 2.3.2: "approximately fifteen per cent of the control group
        # mean (for the treated, against the untreated mean)". v4.8 named the
        # base; on the eligible population the same ratio is 16.9 per cent.
        ("fifteen per cent: ATT against the untreated mean",
         100 * vals["ATT"] / vals["y_untreated"], 15.0, 0.5),
        ("$5,157 true ATE", vals["ATE"], 5157, 700),
    ]
    for label, got, want, tol in claims:
        record(L, f"claim: {label}", close(float(got), want, tol),
               f"chapter {want:,} · data {got:,.2f}" if isinstance(got, float)
               else f"chapter {want:,} · data {got:,}")


# ===========================================================================
# E, Chapter 5 onwards: every results table, cell by cell
# ===========================================================================
#
# Chapters 2 to 4 hold the prose to a hand-written list of claims. Chapter 5
# has eight results tables and around sixty numbers in its prose, most of them
# produced by a script that takes eight minutes, and a hand-written list would
# drift from the manuscript as quickly as the manuscript drifts from the data.
# So the tables are parsed out of the manuscript and every cell is compared
# with the data at the precision it is printed to, and each prose claim is
# held to two things: the sentence is still in the chapter, and the number in
# it still agrees with the data.

def _num(x: str) -> float:
    x = (x.replace("−", "-").replace("$", "").replace(",", "")
         .replace("%", "").replace("+", "").strip())
    return float(x)


def _agrees(got: float, shown: str) -> bool:
    """True if `got`, rounded as `shown` is printed, gives `shown`."""
    t = shown.replace("−", "-").replace(",", "").replace("%", "").replace("$", "")
    dec = len(t.split(".")[1]) if "." in t else 0
    return abs(float(got) - _num(shown)) <= 0.5 * 10 ** -dec + 1e-9


def ms_table(s: str, num: str):
    """(header, rows, caption) of manuscript table `num`, or None."""
    i = s.find(f'["tab", "{num}"')
    if i < 0:
        return None
    j = s.find("\n],\n", i)
    block = s[i:j]
    lists = [json.loads("[" + m + "]") for m in re.findall(
        r'^\s*\[("(?:[^"\\]|\\.)*"(?:, "(?:[^"\\]|\\.)*")*)\],?\s*$', block, re.M)]
    cap = re.search(r'\n\s*\],\n\s*"((?:[^"\\]|\\.)*)",\n', block)
    caption = json.loads('"' + cap.group(1) + '"') if cap else ""
    return lists[0], lists[1:-1], caption


def layer_e5(s: str, repo: Path, data: Path, results: Path) -> None:
    L = "E chapter 5"
    # The manuscript writes a minus sign as the JavaScript escape \u2212.
    prose = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)

    def cell(check, got, shown):
        record(L, check, _agrees(got, shown), f"chapter {shown} · data {got:,.3f}")

    def claim(label, snippet, got, shown=None, ok=None):
        """The sentence is still there, and its number still agrees."""
        present = snippet.lower() in prose.lower()
        if not present:
            record(L, f"claim: {label}", False, f"text not found: '{snippet}'")
            return
        if ok is None:
            ok = _agrees(got, shown)
        det = (f"chapter {shown} · data {got:,.3f}" if shown is not None
               else f"data {got:,.3f}" if isinstance(got, (int, float)) else str(got))
        record(L, f"claim: {label}", ok, det)

    # -- results from Script 5.3 --------------------------------------------
    f1, f2 = results / "matching_results.csv", results / "matching_mahalanobis.csv"
    have = f1.exists() and f2.exists()
    record(L, "Script 5.3 results present", have,
           "" if have else f"run ch05/05_03_compare_variants.py first ({results})")
    if have:
        t = pd.read_csv(f1)
        mh = pd.read_csv(f2)
        seeds = sorted(t.seed.unique())
        record(L, "Script 5.3 results cover six draws", len(seeds) == 6,
               f"{len(seeds)} draw(s); --quick output cannot be audited")
    # A --quick run overwrites the results with a single draw. Stop here
    # rather than fail on every cell that needs a draw it does not have.
    have = have and len(seeds) == 6
    if have:
        mv = t[~t.variant.str.startswith("_")]
        g = mv.groupby("variant").agg(
            bias=("bias", "mean"), sd=("bias", "std"), se=("se", "mean"),
            pairs=("pairs", "mean"), unmatched=("unmatched", "mean"),
            reuse=("max_reuse", "mean"), shift=("att_shift", "mean"))

        # Table 5.2 and Table 5.5: one row per variant
        colmap = {"Bias": "bias", "sd": "sd", "sd of bias": "sd", "Std. error": "se",
                  "Pairs": "pairs", "Unmatched": "unmatched", "Max reuse": "reuse"}
        for num in ("5.2", "5.5"):
            tb = ms_table(s, num)
            if tb is None:
                record(L, f"Table {num} found", False)
                continue
            head, rows, _ = tb
            for r in rows:
                if r[0] not in g.index:
                    record(L, f"Table {num} row is a real variant", False, r[0])
                    continue
                for h, v in zip(head[1:], r[1:]):
                    cell(f"Table {num} {r[0]} · {h}", g.loc[r[0], colmap[h]], v)

        # Table 5.3: the four calipers, by draw
        cal = mv[mv.variant.str.startswith("NN 1:1, caliper")]
        w = cal.pivot(index="seed", columns="variant", values="bias")
        head, rows, cap = ms_table(s, "5.3")
        spread = w.max(axis=1) - w.min(axis=1)
        for r in rows:
            sd_ = int(r[0])
            for h, v in zip(head[1:5], r[1:5]):
                cell(f"Table 5.3 {r[0]} · {h}",
                     w.loc[sd_, f"NN 1:1, caliper {float(h):g}"], v)
            cell(f"Table 5.3 {r[0]} · spread", spread.loc[sd_], r[5])
        colsd = w.std()
        record(L, "Table 5.3 caption: every column sd is 8.5",
               all(_agrees(x, "8.5") for x in colsd) and "8.5 percentage points" in cap,
               ", ".join(f"{x:.2f}" for x in colsd))

        # Table 5.4: Mahalanobis against PS, paired, twelve draws
        m = mh.pivot(index="seed", columns="variant", values="bias")
        m18 = m.pop("_maha18") if "_maha18" in m.columns else None
        m.columns = ["M", "PS"]
        m["red"] = m.PS.abs() - m.M.abs()
        head, rows, cap = ms_table(s, "5.4")
        record(L, "Table 5.4 has one row per draw", len(rows) == len(m),
               f"table {len(rows)} · data {len(m)}")
        for r in rows:
            sd_ = int(r[0])
            if sd_ not in m.index:
                record(L, f"Table 5.4 draw {r[0]} in data", False)
                continue
            cell(f"Table 5.4 {r[0]} · Mahalanobis", m.loc[sd_, "M"], r[1])
            cell(f"Table 5.4 {r[0]} · propensity score", m.loc[sd_, "PS"], r[2])
            cell(f"Table 5.4 {r[0]} · reduction", m.loc[sd_, "red"], r[3])
            better = "Mahalanobis" if m.loc[sd_, "red"] > 0 else "Propensity score"
            record(L, f"Table 5.4 {r[0]} · better", r[4] == better, better)
        mu, sdr = m.red.mean(), m.red.std()
        se = sdr / np.sqrt(len(m))
        first6 = m.loc[seeds, "red"]
        nb = int((m.red > 0).sum())
        words = {6: "six", 11: "eleven", 12: "twelve", 10: "ten", 9: "nine"}
        for lab, snip, got, shown in [
                ("mean", "Mean +6.63 percentage points", mu, "6.63"),
                ("standard deviation", "standard deviation 7.27", sdr, "7.27"),
                ("standard error", "standard error 2.10", se, "2.10")]:
            claim(f"Table 5.4 caption {lab}", snip, got, shown)
        claim("Mahalanobis better in eleven of twelve",
              f"better in {words.get(nb, nb)} draws of {words.get(len(m), len(m))}",
              nb, ok=True)
        claim("Mahalanobis mean reduction 6.63 pp", "average of 6.63 percentage points",
              mu, "6.63")
        claim("... against a standard error of 2.10", "standard error of 2.10", se, "2.10")
        claim("first six draws: mean reduction 7.60", "mean reduction was 7.60",
              first6.mean(), "7.60")
        claim("first six draws: sd 10.13", "standard deviation of 10.13",
              first6.std(), "10.13")
        claim("absolute bias 12.4 (PS)", "from 12.4 per cent to 5.8 per cent",
              m.PS.abs().mean(), "12.4")
        claim("absolute bias 5.8 (Mahalanobis)", "from 12.4 per cent to 5.8 per cent",
              m.M.abs().mean(), "5.8")
        claim("Section 5.6 repeats 5.8 against 12.4", "5.8 per cent against 12.4",
              m.M.abs().mean(), "5.8")

        # Section 5.6: all eighteen covariates in the distance against the four.
        # Until v5.2 the chapter said eighteen "performs considerably worse"
        # with no script measuring it; measured, eighteen does better.
        record(L, "Script 5.3 measures Mahalanobis over all eighteen", m18 is not None,
               "" if m18 is not None else "no _maha18 rows; rerun Script 5.3")
        if m18 is not None:
            red18 = m.M.abs() - m18.abs()
            n18 = int((red18 > 0).sum())
            claim("Section 5.6: four covariates, mean absolute bias 5.8",
                  "from 5.8 to 3.7 per cent", m.M.abs().mean(), "5.8")
            claim("Section 5.6: eighteen covariates, mean absolute bias 3.7",
                  "from 5.8 to 3.7 per cent", m18.abs().mean(), "3.7")
            claim("Section 5.6: eighteen better in nine draws of twelve",
                  f"did better in {words.get(n18, n18)} draws of {words.get(len(red18), len(red18))}",
                  n18, ok=True)
            claim("Section 5.6: mean paired reduction 2.07", "average of 2.07 percentage points",
                  red18.mean(), "2.07")
            claim("Section 5.6: standard error 0.84", "standard error of 0.84",
                  red18.std() / np.sqrt(len(red18)), "0.84")
            record(L, "Section 5.6 no longer says eighteen performs worse",
                   "performs considerably worse" not in prose)

        # Section 5.5: caliper against draw
        claim("caliper moves the estimate by 0.09 on average",
              "average of 0.09 percentage points", spread.mean(), "0.09")
        claim("... and never by more than 0.16", "never by more than 0.16",
              spread.max(), "0.16")
        claim("less than a fifth of a point", "less than a fifth of a percentage point",
              spread.max(), ok=spread.max() < 0.2)
        claim("draw-to-draw sd 8.5", "draw-to-draw standard deviation is 8.5",
              colsd.mean(), "8.5")
        lo, hi = w.values.max(), w.values.min()
        claim("estimate ranges from -2.8", "ranges from −2.8", lo, "-2.8")
        claim("... to -23.7", "to −23.7 per cent", hi, "-23.7")
        ratio = colsd.mean() / spread.mean()
        claim("the draw matters about ninety times more", "about ninety times more",
              ratio, ok=80 <= ratio < 100)
        claim("16 unmatched at 0.02 against 3 at 0.2", "leaves sixteen treated persons",
              g.loc["NN 1:1, caliper 0.02", "unmatched"],
              ok=_agrees(g.loc["NN 1:1, caliper 0.02", "unmatched"], "16")
              and _agrees(g.loc["NN 1:1, caliper 0.2", "unmatched"], "3"))

        # Section 5.4: eight rows within about a point, the ninth fifteen away
        eight = g.drop("Mahalanobis within caliper 0.1").bias
        claim("first eight rows differ by about one point",
              "differ from one another by about one percentage point",
              eight.max() - eight.min(), ok=eight.max() - eight.min() < 1.5)
        gap = g.loc["Mahalanobis within caliper 0.1", "bias"] - \
            g.loc["NN 1:1, caliper 0.1", "bias"]
        claim("the ninth differs by fifteen", "the ninth differs from them by fifteen",
              gap, ok=14.5 <= gap < 15.5)

        # Section 5.7: ratio matching
        claim("1:3 sd falls from 8.5", "from 8.5 to 5.1",
              g.loc["NN 1:1, caliper 0.1", "sd"], "8.5")
        claim("... to 5.1", "from 8.5 to 5.1", g.loc["NN 1:3, caliper 0.1", "sd"], "5.1")
        claim("1:3 leaves 63 unmatched against 5", "leaves 63 treated persons unmatched",
              g.loc["NN 1:3, caliper 0.1", "unmatched"], "63")
        _, _, cap5 = ms_table(s, "5.5")
        claim("Table 5.5 caption: sd falls 40 per cent",
              "standard deviation falls by 40 per cent",
              100 * (1 - g.loc["NN 1:3, caliper 0.1", "sd"] / g.loc["NN 1:1, caliper 0.1", "sd"]),
              "40")
        claim("Table 5.5 caption: naive se falls 41 per cent",
              "naive standard error by 41 per cent",
              100 * (1 - g.loc["NN 1:3, caliper 0.1", "se"] / g.loc["NN 1:1, caliper 0.1", "se"]),
              "41")

        # Table 5.6 and Section 5.8: optimal against greedy
        o = t[t.variant.isin(["_optimal", "_greedy_same"])].pivot(
            index="seed", columns="variant", values=["bias", "dist", "pairs"])
        ob, gb = o[("bias", "_optimal")], o[("bias", "_greedy_same")]
        diff = gb.abs() - ob.abs()
        dist = 100 * (o[("dist", "_optimal")] / o[("dist", "_greedy_same")] - 1)
        _, rows, cap = ms_table(s, "5.6")
        for r in rows:
            sd_ = int(r[0])
            cell(f"Table 5.6 {r[0]} · optimal", ob.loc[sd_], r[1])
            cell(f"Table 5.6 {r[0]} · greedy", gb.loc[sd_], r[2])
            cell(f"Table 5.6 {r[0]} · difference", diff.loc[sd_], r[3])
            cell(f"Table 5.6 {r[0]} · total distance", dist.loc[sd_], r[4])
        claim("Table 5.6 caption: 2,462 pairs on average", "2,462 on average",
              o[("pairs", "_optimal")].mean(), "2,462")
        claim("optimal cuts total distance by 31 per cent on average",
              "by 31 per cent on average", -dist.mean(), "31")
        claim("optimal better in six draws of six", "six draws of six",
              int((diff > 0).sum()), ok=int((diff > 0).sum()) == 6)
        claim("improvement 1.47 pp", "improvement is 1.47 percentage points",
              diff.mean(), "1.47")
        claim("... sd 1.33", "standard deviation across draws of 1.33", diff.std(), "1.33")
        claim("optimal column runs from -3.2", "runs from −3.2", ob.max(), "-3.2")
        claim("... to -32.0", "to −32.0 per cent", ob.min(), "-32.0")

        # Table 5.7 and Section 5.12: regression adjustment
        ra = t[t.variant.isin(["_ra_ps", "_ra_maha"])]
        _, rows, _ = ms_table(s, "5.7")
        key = {"Propensity score nearest neighbour": "_ra_ps",
               "Mahalanobis within a caliper": "_ra_maha"}
        for r in rows:
            q = ra[ra.variant == key[r[0]]]
            cell(f"Table 5.7 {r[0]} · plain", q.bias.mean(), r[1])
            cell(f"Table 5.7 {r[0]} · bias-corrected", q.biascorr.mean(), r[2])
            cell(f"Table 5.7 {r[0]} · regression-adjusted", q.regadj.mean(), r[3])
            k_bc = int((q.biascorr.abs() < q.bias.abs()).sum())
            k_ra = int((q.regadj.abs() < q.bias.abs()).sum())
            k = int(re.match(r"(\d+)", r[4]).group(1))
            record(L, f"Table 5.7 {r[0]} · improved in", k in (k_bc, k_ra),
                   f"chapter {r[4]} · data bias-corrected {k_bc}, "
                   f"regression-adjusted {k_ra} of {len(q)}")

        # Section 5.4: why the comparisons are untrimmed, and the check that
        # trimming would change none of the findings.
        tr = t[t.variant.isin(["_trim_ps", "_trim_maha"])]
        one = tr[tr.variant == "_trim_ps"]
        record(L, "Script 5.3 results include the trimming check", len(one) == len(seeds),
               f"{len(one)} draw(s)")
        if len(one):
            claim("no score approaches the upper threshold",
                  "no score approaches the upper threshold", one.max_ps.max(),
                  ok=bool((one.max_ps < 1 - one.alpha).all()) and one.max_ps.max() < 0.8)
            claim("trim removes 89 treated", "the six draws, 89 treated persons",
                  one.treated_removed.mean(), "89")
            claim("... all with scores below 0.045", "with scores below 0.045",
                  one.max_ps_removed_treated.max(),
                  ok=bool(one.max_ps_removed_treated.max() < 0.045))
            claim("... together with 2,649 controls", "together with 2,649 controls",
                  one.controls_removed.mean(), "2,649")
            claim("every removed treated person matches untrimmed",
                  "Every one of those 89 treated persons finds a control",
                  one.removed_were_matched.sum(),
                  ok=bool((one.removed_were_matched == one.treated_removed).all()))
            claim("trim raises the true ATT by 1.1 per cent", "raises the true ATT by 1.1",
                  (100 * (one.att_kept / one.att_all - 1)).mean(), "1.1")
            claim("the caliper discards about five", "discards about five treated persons",
                  g.loc["NN 1:1, caliper 0.1", "unmatched"], "5")
            claim("trimmed PS matching -12.6", "from \u221214.4 to \u221212.6 per cent",
                  tr[tr.variant == "_trim_ps"].bias.mean(), "-12.6")
            claim("untrimmed PS matching -14.4", "from \u221214.4 to \u221212.6 per cent",
                  g.loc["NN 1:1, caliper 0.1", "bias"], "-14.4")
            claim("trimmed Mahalanobis -0.4", "from +0.7 to \u22120.4 per cent",
                  tr[tr.variant == "_trim_maha"].bias.mean(), "-0.4")
            same_order = (abs(tr[tr.variant == "_trim_maha"].bias.mean())
                          < abs(tr[tr.variant == "_trim_ps"].bias.mean()))
            claim("the ordering is the same either way", "the same either way",
                  0, ok=bool(same_order))

        # Section 5.11: the estimand. These are six-draw means, like the rest
        # of the chapter's matching results; the primary dataset alone gives
        # $6,405 against $6,408, and 0.07 and 0.55 per cent.
        c01 = mv[mv.variant == "NN 1:1, caliper 0.1"]
        claim("true ATT among matched $6,443", "among those matched is $6,443",
              c01.att_matched.mean(), "$6,443")
        claim("true ATT among all treated $6,446", "against $6,446 among all eligible treated persons",
              c01.att_all.mean(), "$6,446")
        claim("shift 0.05 per cent", "a shift of 0.05 per cent",
              abs(g.loc["NN 1:1, caliper 0.1", "shift"]), "0.05")
        claim("tightest caliper shift 0.15 per cent", "tightest caliper the shift is 0.15",
              abs(g.loc["NN 1:1, caliper 0.02", "shift"]), "0.15")
        claim("1:3 shift 0.8 per cent", "it is 0.8 per cent",
              abs(g.loc["NN 1:3, caliper 0.1", "shift"]), "0.8")
        claim("about five unmatched at 0.1", "about five of the 4,823 treated persons",
              g.loc["NN 1:1, caliper 0.1", "unmatched"], "5")
        claim("... of 4,823 treated on average", "about five of the 4,823 treated persons",
              g.loc["NN 1:1, no caliper", "pairs"], "4,823")
        claim("Section 5.7: sixty-three of 4,823", "Sixty-three of 4,823",
              g.loc["NN 1:3, caliper 0.1", "unmatched"],
              ok=_agrees(g.loc["NN 1:3, caliper 0.1", "unmatched"], "63")
              and _agrees(g.loc["NN 1:1, no caliper", "pairs"], "4,823"))
        claim("Section 5.6: the Mahalanobis result rests on twelve draws",
              "holds in twelve draws", len(m), ok=len(m) == 12)

        # Section 5.16.2: the accounting
        claim("5.16.2 distance 6.6", "distance measure reduces the absolute bias by 6.6",
              mu, "6.6")
        rat = abs(g.loc["NN 1:1, caliper 0.1", "bias"]) - abs(g.loc["NN 1:2, caliper 0.1", "bias"])
        claim("5.16.2 ratio 1.2", "the ratio moves the estimate by 1.2", rat, "1.2")
        rep_ = abs(g.loc["NN 1:1, caliper 0.1", "bias"]) - \
            abs(g.loc["NN 1:1 with replacement, caliper 0.1", "bias"])
        claim("5.16.2 replacement 0.5", "replacement by 0.5", rep_, "0.5")
        claim("5.16.2 caliper 0.09", "the caliper by 0.09", spread.mean(), "0.09")
        claim("5.16.2 draw 8.5", "The draw moves it by 8.5", colsd.mean(), "8.5")

    # -- primary dataset: Sections 5.8, 5.10, 5.11 and Table 5.8 ------------
    if not (data / "analysis_file.csv").exists():
        for scr in ("ch02/02_05_link_modules.py", "ch02/02_06_reshape_panel.py"):
            subprocess.run([sys.executable, str(repo / scr), "--datadir", str(data)],
                           check=True, capture_output=True)
    sys.path.insert(0, str(repo / "ch05"))
    from _common5 import score, nn_match, mahalanobis_match, smd   # noqa: E402
    sc = score(data, "logit", with_truth=True)
    X, D, ps, tau = sc["X"], sc["D"], sc["ps"], sc["tau"]
    nt, nc = int(D.sum()), int((D == 0).sum())
    claim("4,867 treated and 37,708 controls", "4,867 treated persons against 37,708",
          nt, ok=(nt, nc) == (4867, 37708))

    mt, mc = nn_match(ps, D, 0.1, replace=True, ratio=1)
    v = pd.Series(mc).value_counts()
    claim("with replacement: 4,864 pairs", "Of the 4,864 pairs", len(mt), "4,864")
    claim("... 4,290 distinct controls", "4,290 distinct controls", v.size, "4,290")
    claim("... 3,803 used once", "3,803 of them appear exactly once",
          int((v == 1).sum()), "3,803")
    claim("... most-used four times", "up to four times at a 0.1 caliper",
          int(v.max()), ok=int(v.max()) == 4)


    mtp, mcp = nn_match(ps, D, 0.1, False, 1)
    mtm, mcm = mahalanobis_match(X, D, ps, 0.1)
    labels = {"log earnings 2016": "log_inc_2016", "fortnights on payment": "fn_2016",
              "long-term recipient": "lts", "age": "age", "highest education": "edu",
              "remoteness": "remote", "SEIFA decile": "seifa", "mental health item": "mh"}
    _, rows, _ = ms_table(s, "5.8")
    got = []
    for r in rows:
        if r[0] not in labels:
            continue
        x = X[labels[r[0]]].values
        pooled = np.sqrt((x[D == 1].var() + x[D == 0].var()) / 2)
        b = smd(x, D == 1, D == 0)
        a1 = (x[mtp].mean() - x[mcp].mean()) / pooled
        a2 = (x[mtm].mean() - x[mcm].mean()) / pooled
        got.append((b, a1, a2))
        for h, val, shown in zip(("before", "PS", "Mahalanobis"), (b, a1, a2), r[1:4]):
            cell(f"Table 5.8 {r[0]} · {h}", val, shown)
    A = np.abs(np.array(got))
    summ = {r[0]: r for r in rows}
    for k, lab in enumerate(("before", "PS", "Mahalanobis")):
        cell(f"Table 5.8 mean absolute · {lab}", A[:, k].mean(),
             summ["Mean absolute difference"][k + 1])
        cell(f"Table 5.8 largest absolute · {lab}", A[:, k].max(),
             summ["Largest absolute difference"][k + 1])
        above = int((A[:, k] > 0.1).sum())
        record(L, f"Table 5.8 above 0.1 · {lab}",
               summ["Covariates above 0.1"][k + 1] == f"{above} of {len(A)}",
               f"{above} of {len(A)}")
    if have:
        for k, v_ in (("Propensity score", "NN 1:1, caliper 0.1"),
                      ("Mahalanobis", "Mahalanobis within caliper 0.1")):
            col = {"Propensity score": 2, "Mahalanobis": 3}[k]
            cell(f"Table 5.8 bias row · {k}", g.loc[v_, "bias"],
                 summ["Bias of the resulting ATT"][col])
    claim("5.15 mean absolute 0.005 and 0.015 against 0.284",
          "0.005 and 0.015 against 0.284", A[:, 1].mean(), "0.005")

    # -- numbers with no script behind them ---------------------------------
    # Every number in the chapter has to be reproducible from a script in
    # Table 5.9. Draft v1.0 quoted a coarsened exact matching estimate in
    # Section 5.9 that no script produced; v1.2 cut the figures and kept the
    # argument. This holds the section to that: it may discuss the method, but
    # it may not report a result for it unless a script appears that does.
    s59 = re.search(r'\["h2", "5\.9 .*?\["h2", "5\.10', prose, re.S)
    src = " ".join(p.read_text() for p in (repo / "ch05").glob("*.py"))
    figs = re.findall(r"\d+(?:\.\d+)? per cent|\d[\d,]*\d usable strata|\$\d[\d,]*",
                      s59.group(0)) if s59 else []
    record(L, "Section 5.9 reports no unscripted coarsened-matching result",
           bool(s59) and (not figs or "coarsen" in src.lower()),
           f"figures in Section 5.9: {figs}" if figs else "")



# ===========================================================================
# E, Chapter 4: every results table, cell by cell
# ===========================================================================
#
# Added in v4.8, on the Chapter 5 model. Tables 4.1, 4.2 and 4.5 are primary-
# dataset exhibits and are recomputed here; Tables 4.3 and 4.4 come from the
# five-draw results Script 4.3 writes (figures/trimming_results.csv). The
# helpers of Scripts 4.1 and 4.4 are imported rather than reimplemented,
# because what is being tested is whether the manuscript still says what the
# scripts produce.

def _load_script(path: Path, name: str):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rule_key(rules: dict, label: str):
    n = label.split()[0]
    hits = [k for k in rules if k.split()[0] == n]
    return hits[0] if hits else None


def layer_e4(s: str, repo: Path, data: Path, results: Path) -> None:
    L = "E chapter 4"

    def cell(check, got, shown):
        record(L, check, _agrees(got, shown), f"chapter {shown} · data {got:,.4f}")

    if not (data / "analysis_file.csv").exists():
        for scr in ("ch02/02_05_link_modules.py", "ch02/02_06_reshape_panel.py"):
            subprocess.run([sys.executable, str(repo / scr), "--datadir", str(data)],
                           check=True, capture_output=True)
    sys.path.insert(0, str(repo / "ch04"))
    from _common4 import score, trimming_rules, crump_alpha          # noqa: E402
    s41 = _load_script(repo / "ch04" / "04_01_assess_overlap.py", "s41")
    s44 = _load_script(repo / "ch04" / "04_04_who_is_removed.py", "s44")

    # -- Table 4.1: overlap under the two scores -----------------------------
    got = {}
    for label, est in (("Logistic", "logit"), ("Boosting", "gbm")):
        sc = score(data, est)
        got[label] = s41.counts(sc["ps"], sc["D"])
    head, rows, _ = ms_table(s, "4.1")
    for r in rows:
        for h, v in zip(head[1:3], r[1:3]):
            want = got[h].get(r[0])
            record(L, f"Table 4.1 {r[0]} · {h}", want == v,
                   f"chapter {v} · data {want}")

    # -- Table 4.2: what each rule removes, logistic score --------------------
    sc = score(data, "logit", with_truth=True)
    E, ps, D, tau = sc["E"], sc["ps"], sc["D"], sc["tau"]
    R = trimming_rules(ps, D)
    head, rows, _ = ms_table(s, "4.2")
    for r in rows:
        k = _rule_key(R, r[0])
        if k is None:
            record(L, f"Table 4.2 row is a real rule: {r[0]}", False)
            continue
        drop = ~R[k]
        for h, val, shown in [("removed", drop.sum(), r[1]),
                              ("treated", (drop & (D == 1)).sum(), r[2]),
                              ("controls", (drop & (D == 0)).sum(), r[3]),
                              ("share", 100 * drop.mean(), r[4])]:
            cell(f"Table 4.2 rule {r[0].split()[0]} · {h}", float(val), shown)
        a_ = re.search(r"alpha = ([\d.]+)", r[0])
        if a_:
            cell("Table 4.2 variance-minimising alpha", crump_alpha(ps), a_.group(1))

    # -- Table 4.5: who rule 3 removes ----------------------------------------
    keep = R[s44.DEFAULT_RULE]
    drop = ~keep
    head, rows, _ = ms_table(s, "4.5")
    vals = {"Persons": (keep.sum(), drop.sum()),
            "Commenced the programme": (100 * D[keep].mean(), 100 * D[drop].mean()),
            "True average effect": (tau[keep].mean(), tau[drop].mean())}
    for label, col, _fmt in s44.DESCRIBE:
        v = E[col].fillna(0).values
        vals[label] = (v[keep].mean(), v[drop].mean())
    for r in rows:
        if r[0] not in vals:
            record(L, f"Table 4.5 row is computed: {r[0]}", False)
            continue
        cell(f"Table 4.5 {r[0]} · retained", float(vals[r[0]][0]), r[1])
        cell(f"Table 4.5 {r[0]} · removed", float(vals[r[0]][1]), r[2])

    # -- Tables 4.3 and 4.4: Script 4.3's five draws --------------------------
    f = results / "trimming_results.csv"
    record(L, "Script 4.3 results present", f.exists(),
           "" if f.exists() else f"run ch04/04_03_compare_rules.py first ({results})")
    if not f.exists():
        return
    t = pd.read_csv(f)
    seeds = sorted(t.seed.unique())
    record(L, "Script 4.3 results cover five draws", len(seeds) == 5,
           f"{len(seeds)} draw(s); --quick output cannot be audited")
    if len(seeds) != 5:
        return
    g = t.pivot_table(index="rule", columns="score",
                      values=["ate_bias", "att_bias"], aggfunc="mean")
    head, rows, _ = ms_table(s, "4.3")
    colmap = {"ATE logit": ("ate_bias", "logit"), "ATT logit": ("att_bias", "logit"),
              "ATE boost": ("ate_bias", "gbm"), "ATT boost": ("att_bias", "gbm")}
    for r in rows:
        k = _rule_key({x: 1 for x in g.index}, r[0])
        for h, v in zip(head[1:], r[1:]):
            cell(f"Table 4.3 rule {r[0].split()[0]} · {h}", g.loc[k, colmap[h]], v)

    # Table 4.4 says "one draw" and "seed 20260808"; check it against that
    # draw, and report the five-draw means beside it.
    one = t[(t.score == "logit") & (t.seed == 20260808)].set_index("rule")
    five = t[t.score == "logit"].groupby("rule")[["retained", "se_ate", "se_att"]].mean()
    head, rows, cap = ms_table(s, "4.4")
    base = one.loc[_rule_key({x: 1 for x in one.index}, "0"), "se_ate"]
    for r in rows:
        k = _rule_key({x: 1 for x in one.index}, r[0])
        n_ = r[0].split()[0]
        cell(f"Table 4.4 rule {n_} · retained", float(one.loc[k, "retained"]), r[1])
        cell(f"Table 4.4 rule {n_} · SE of the ATE", one.loc[k, "se_ate"], r[2])
        cell(f"Table 4.4 rule {n_} · SE of the ATT", one.loc[k, "se_att"], r[3])
        if r[4] not in ("—", "-"):
            cell(f"Table 4.4 rule {n_} · change in SE(ATE)",
                 100 * (one.loc[k, "se_ate"] / base - 1), r[4])
        record(L, f"Table 4.4 rule {n_} · five-draw means, for comparison", None,
               f"retained {five.loc[k, 'retained']:,.0f} · SE(ATE) {five.loc[k, 'se_ate']:,.0f}"
               f" · SE(ATT) {five.loc[k, 'se_att']:,.0f}")



# ===========================================================================
# E, Chapter 3: every results table, cell by cell
# ===========================================================================
#
# Added in v4.9, on the Chapter 4 and 5 model. Tables 3.1, 3.2 and 3.6, and the
# primary-dataset rows of Table 3.4, are recomputed here. Tables 3.3 and 3.5,
# and the five-draw rows of Table 3.4, come from the results Scripts 3.5 and
# 3.7 write (figures/specification_results.csv, near_instrument_results.csv).

T36_KEYS = {
    "Score range": "range",
    "Mean score against observed rate": "mean vs rate",
    "Largest stabilised weight": "largest stabilised weight",
    "Effective control sample (stabilised)": "effective control sample",
    "Treated above the highest control score": "treated above highest control",
    "Controls below the lowest treated score": "controls below lowest treated",
    "Persons with a score above 0.5": "persons with a score above 0.5",
    "Persons with a score above 0.7": "persons with a score above 0.7",
    "Smallest decile treated cell": "smallest decile treated cell",
}


def layer_e3(s: str, repo: Path, data: Path, results: Path) -> None:
    L = "E chapter 3"
    prose = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)

    def cell(check, got, shown):
        record(L, check, _agrees(got, shown), f"chapter {shown} · data {got:,.4f}")

    def claim(label, snippet, got, shown=None, ok=None):
        if snippet.lower() not in prose.lower():
            record(L, f"claim: {label}", False, f"text not found: '{snippet}'")
            return
        ok = _agrees(got, shown) if ok is None else ok
        record(L, f"claim: {label}", ok,
               f"chapter {shown} · data {got:,.4f}" if shown else f"data {got:,.4f}")

    if not (data / "analysis_file.csv").exists():
        for scr in ("ch02/02_05_link_modules.py", "ch02/02_06_reshape_panel.py"):
            subprocess.run([sys.executable, str(repo / scr), "--datadir", str(data)],
                           check=True, capture_output=True)
    sys.path.insert(0, str(repo / "ch03"))
    from _common3 import (load_analysis, eligible_only, design_matrix,   # noqa: E402
                          fit_propensity)
    from sklearn.linear_model import LogisticRegression                  # noqa: E402
    from sklearn.metrics import roc_auc_score                            # noqa: E402
    s32 = _load_script(repo / "ch03" / "03_02_estimate_logit.py", "s32")
    s36 = _load_script(repo / "ch03" / "03_06_diagnose_score.py", "s36")

    E = eligible_only(load_analysis(data))
    X, D = design_matrix(E), E["treated"].values

    # -- Table 3.1: what enters the model -------------------------------------
    _, rows, cap = ms_table(s, "3.1")
    n_cols = X.shape[1]
    words = {18: "Eighteen", 19: "Nineteen", 20: "Twenty", 21: "Twenty-one"}
    record(L, "Table 3.1 caption: twenty numeric columns enter the model",
           cap.startswith(f"{words.get(n_cols, n_cols)} numeric columns"),
           f"design matrix has {n_cols} columns")
    # Draft v1.0 said twenty in six places, here and in Chapter 5; the design
    # matrix has had eighteen columns throughout v1.1.0.
    w_ = words.get(n_cols, str(n_cols)).lower()
    for snip in (f"conditioned on {w_}.", f"{w_} columns enter, drawn",
                 f"on the {w_} covariates, fitted on the 42,575 persons"):
        claim(f"covariate count: '{snip}'", snip, float(n_cols), ok=True)
    stale = re.findall(r"\b(?:twenty|nineteen)\b(?!-two| seconds| minutes| points)",
                       prose.lower())
    stale = [x for x in stale if x != w_]
    record(L, "no other covariate count in the chapter", not stale, f"found: {stale}")
    record(L, "Section 3.4.1 fits on the eligible population", len(X) == 42575,
           f"{len(X):,} persons")
    held = [r[0] for r in rows if r[2].startswith(("Held back", "Excluded"))]
    leaked = [h for h in held if h in X.columns]
    record(L, "Table 3.1 held-back covariates are not in the design matrix",
           not leaked, f"in the model: {leaked}" if leaked else ", ".join(held))

    # -- Table 3.2: standardised logistic coefficients ------------------------
    Z = (X - X.mean()) / X.std().replace(0, 1)
    m = LogisticRegression(max_iter=5000, C=1e6).fit(Z, D)
    ps = m.predict_proba(Z)[:, 1]
    p = np.clip(ps, 1e-9, 1 - 1e-9)
    Zi = np.c_[np.ones(len(Z)), Z.values]
    se = np.sqrt(np.diag(np.linalg.pinv(Zi.T @ (Zi * (p * (1 - p))[:, None]))))[1:]
    co = pd.Series(m.coef_[0], index=X.columns)
    sd = pd.Series(se, index=X.columns)
    top = list(co.abs().sort_values(ascending=False).index[:8])
    _, rows, cap = ms_table(s, "3.2")
    labels = [s32.LABEL.get(k, k) for k in top]
    record(L, "Table 3.2 lists the eight largest, in order",
           [r[0] for r in rows] == labels, f"data order: {labels}")
    inv = {s32.LABEL.get(k, k): k for k in X.columns}
    for r in rows:
        k = inv.get(r[0])
        if k is None:
            record(L, f"Table 3.2 row is a covariate: {r[0]}", False)
            continue
        cell(f"Table 3.2 {r[0]} · coefficient", co[k], r[1])
        cell(f"Table 3.2 {r[0]} · std. error", sd[k], r[2])
        cell(f"Table 3.2 {r[0]} · z", co[k] / sd[k], r[3])
    ic = re.search(r"Intercept (\S+?);", cap)
    au = re.search(r"area under the curve (\d+\.\d+)", cap)
    nn = re.search(r"n = ([\d,]+)", cap)
    if ic:
        cell("Table 3.2 caption intercept", m.intercept_[0], ic.group(1))
    if au:
        cell("Table 3.2 caption AUC", roc_auc_score(D, ps), au.group(1))
    if nn:
        cell("Table 3.2 caption n", float(len(X)), nn.group(1))

    # -- Table 3.6: diagnostics, and the primary rows of Table 3.4 ------------
    scores = {"Logistic": fit_propensity(X, D, "logit"),
              "Boosting": fit_propensity(X, D, "gbm", seed=20260808)}
    diag = {k: s36.diagnose(v, D)[0] for k, v in scores.items()}
    _, rows, _ = ms_table(s, "3.6")
    for r in rows:
        key = T36_KEYS.get(r[0])
        for col, v in zip(("Logistic", "Boosting"), r[1:3]):
            want = diag[col].get(key) if key else None
            record(L, f"Table 3.6 {r[0]} · {col}", want == v,
                   f"chapter {v} · data {want}")

    head, rows, cap = ms_table(s, "3.4")
    t34 = {r[0]: r for r in rows}
    for col, k in (("Logistic", 1), ("Boosting", 2)):
        ps_ = scores[col]
        tr, ct = ps_[D == 1], ps_[D == 0]
        cell(f"Table 3.4 AUC · {col}", roc_auc_score(D, ps_),
             t34["Area under the ROC curve"][k])
        want = f"{ps_.min():.3f} to {ps_.max():.3f}"
        record(L, f"Table 3.4 score range · {col}", t34["Score range"][k] == want,
               f"chapter {t34['Score range'][k]} · data {want}")
        cell(f"Table 3.4 treated above the highest control · {col}",
             float((tr > ct.max()).sum()), t34["Treated above the highest control score"][k])
    rc = re.search(r"correlate at (\d+\.\d+)", cap)
    if rc:
        cell("Table 3.4 caption: Pearson correlation of the two scores",
             np.corrcoef(scores["Logistic"], scores["Boosting"])[0, 1], rc.group(1))

    # -- Tables 3.3, 3.4 (five-draw rows) and 3.5: the draws ------------------
    f5 = results / "specification_results.csv"
    f7 = results / "near_instrument_results.csv"
    for f, scr in ((f5, "03_05_specifications"), (f7, "03_07_near_instrument")):
        record(L, f"Script results present: {f.name}", f.exists(),
               "" if f.exists() else f"run ch03/{scr}.py first ({results})")
    if f5.exists():
        t = pd.read_csv(f5)
        ok5 = t.seed.nunique() == 5
        record(L, "Script 3.5 results cover five draws", ok5,
               f"{t.seed.nunique()} draw(s); --quick output cannot be audited")
        if ok5:
            g = t.groupby("spec").agg(auc=("auc", "mean"), bias=("bias", "mean"),
                                      sd=("bias", "std"), unmatched=("unmatched", "mean"),
                                      maxw=("maxw", "mean"))
            head, rows, _ = ms_table(s, "3.3")
            cm = {"AUC": "auc", "Bias": "bias", "sd": "sd", "Unmatched": "unmatched",
                  "Max weight": "maxw"}
            for r in rows:
                k = _rule_key({x: 1 for x in g.index}, r[0])
                for h, v in zip(head[1:], r[1:]):
                    cell(f"Table 3.3 spec {r[0].split()[0]} · {h}", g.loc[k, cm[h]], v)
            s3 = _rule_key({x: 1 for x in g.index}, "3")
            s6 = _rule_key({x: 1 for x in g.index}, "6")
            for label, col in (("Treated left unmatched at a 0.1 caliper", "unmatched"),
                               ("Largest stabilised weight", "maxw"),
                               ("Bias of the matched estimate", "bias"),
                               ("Standard deviation of that bias", "sd")):
                for k, spec in ((1, s3), (2, s6)):
                    cell(f"Table 3.4 {label} · {'Logistic' if k == 1 else 'Boosting'}",
                         g.loc[spec, col], t34[label][k])
            gap = g.loc[s6, "bias"] - g.loc[s3, "bias"]
            claim("Table 3.4: opposite signs, 33 points apart", "33 points apart",
                  gap, ok=_agrees(gap, "33") and g.loc[s3, "bias"] < 0 < g.loc[s6, "bias"])
    if f7.exists():
        t7 = pd.read_csv(f7)
        ok7 = len(t7) == 5
        record(L, "Script 3.7 results cover five draws", ok7,
               f"{len(t7)} draw(s); --quick output cannot be audited")
        if ok7:
            mm, ss = t7.mean(), t7.std()
            _, rows, _ = ms_table(s, "3.5")
            keys = {"Area under the ROC curve": "auc",
                    "Largest stabilised weight": "stabmax",
                    "Largest control odds weight": "oddsmax",
                    "Effective control sample (odds weights)": "ess",
                    "Standard error of the weighted estimate": "se",
                    "Treated left unmatched at a 0.1 caliper": "unmatched",
                    "Bias of the matched estimate": "bias"}
            for r in rows:
                if r[0] == "Standard deviation of that bias":
                    cell("Table 3.5 sd of bias · without", ss["bias_without"], r[1])
                    cell("Table 3.5 sd of bias · with", ss["bias_with"], r[2])
                    continue
                k = keys.get(r[0])
                if k is None:
                    record(L, f"Table 3.5 row is computed: {r[0]}", False)
                    continue
                cell(f"Table 3.5 {r[0]} · without", mm[f"{k}_without"], r[1])
                cell(f"Table 3.5 {r[0]} · with", mm[f"{k}_with"], r[2])
            # The "Change" column
            ch = {r[0]: r[3] for r in rows}
            ratio = lambda k: mm[f"{k}_with"] / mm[f"{k}_without"]      # noqa: E731
            words_n = {"5": 5, "16": 16, "Ten": 10}
            for label, k in (("Largest stabilised weight", "stabmax"),
                             ("Largest control odds weight", "oddsmax"),
                             ("Treated left unmatched at a 0.1 caliper", "unmatched")):
                if ch[label].startswith("More than ten"):
                    ok_ = ratio(k) > 10            # v4.9 wording; "Ten times" was 13.6
                else:
                    n_ = re.match(r"(\d+|Ten)", ch[label])
                    tok = n_.group(1) if n_ else None
                    want = words_n[tok] if tok in words_n else (float(tok) if tok else None)
                    ok_ = want is not None and abs(ratio(k) - want) < 0.5
                record(L, f"Table 3.5 change · {label}", ok_,
                       f"chapter '{ch[label]}' · data {ratio(k):.2f} times")
            cell("Table 3.5 change · controls lost (per cent)",
                 100 * (1 - ratio("ess")),
                 re.match(r"(\d+)", ch["Effective control sample (odds weights)"]).group(1))
            # Chapter 2 states this result in advance (Section 2.4). Until v5.0
            # it quoted an earlier measurement, 28,000 to 4,200, that no
            # longer matched the table; hold it to the draws.
            sib = repo / "manuscript" / "ch02_content.js"
            if sib.exists():
                s2 = sib.read_text()
                m2 = re.search(r"largest stabilised weight about (\w+)fold, widens the "
                               r"standard error of the weighted estimate by ([^,]+), and "
                               r"reduces the effective control sample from roughly "
                               r"(\d[\d,]*\d) to roughly (\d[\d,]*\d)", s2)
                record(L, "Chapter 2's advance statement found", bool(m2))
                if m2:
                    fold = {"five": 5, "six": 6, "four": 4}.get(m2.group(1))
                    record(L, "Chapter 2: weight rises about fivefold",
                           fold is not None and abs(ratio("stabmax") - fold) < 0.5,
                           f"chapter {m2.group(1)}fold · data {ratio('stabmax'):.2f}")
                    se_up = 100 * (ratio("se") - 1)
                    record(L, "Chapter 2: standard error wider by nearly thirty per cent",
                           m2.group(2) == "nearly thirty per cent" and 25 <= se_up < 30,
                           f"chapter '{m2.group(2)}' · data {se_up:.1f}%")
                    for grp, key in ((3, "ess_without"), (4, "ess_with")):
                        want = float(m2.group(grp).replace(",", ""))
                        record(L, f"Chapter 2: effective control sample roughly {m2.group(grp)}",
                               abs(mm[key] - want) / want < 0.05,
                               f"chapter {m2.group(grp)} · data {mm[key]:,.0f}")
            cell("Table 3.5 change · standard error wider (per cent)",
                 100 * (ratio("se") - 1),
                 re.match(r"(\d+)", ch["Standard error of the weighted estimate"]).group(1))



# ===========================================================================
# E, Chapter 6: every results table, cell by cell
# ===========================================================================
#
# Added in v5.0 with the chapter. Table 6.1 is recomputed from Script 6.1's own
# function; Tables 6.2 to 6.6 and 6.8 come from Script 6.2's six draws
# (figures/weighting_results.csv), aggregated by the script's own cell();
# Table 6.7 from Script 6.3's (figures/wrong_reason_results.csv). Each prose
# number is held to its sentence and its value, as in Chapter 5.

def layer_e6(s: str, repo: Path, data: Path, results: Path) -> None:
    L = "E chapter 6"
    prose = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)
    M = "−"

    def cell_(check, got, shown):
        record(L, check, _agrees(got, shown), f"chapter {shown} · data {got:,.4f}")

    def claim(label, snippet, got, shown=None, ok=None):
        if snippet.lower() not in prose.lower():
            record(L, f"claim: {label}", False, f"text not found: '{snippet}'")
            return
        ok = _agrees(got, shown) if ok is None else ok
        record(L, f"claim: {label}", bool(ok),
               f"chapter {shown} · data {got:,.4f}" if shown else f"data {got:,.4f}")

    def pair(text):
        m = re.match(r"([+−-]?[\d.]+)%\s*\(([\d.]+)\)", text)
        return (m.group(1), m.group(2)) if m else (None, None)

    if not (data / "analysis_file.csv").exists():
        for scr in ("ch02/02_05_link_modules.py", "ch02/02_06_reshape_panel.py"):
            subprocess.run([sys.executable, str(repo / scr), "--datadir", str(data)],
                           check=True, capture_output=True)
    s61 = _load_script(repo / "ch06" / "06_01_build_weights.py", "s61")
    s62 = _load_script(repo / "ch06" / "06_02_compare_weighting.py", "s62")

    # -- Table 6.1 -----------------------------------------------------------
    got = s61.table_6_1(data)
    head, rows, _ = ms_table(s, "6.1")
    for r in rows:
        for col, key, v in (("Logistic", "logistic", r[1]), ("Boosting", "boosting", r[2])):
            want = got[key].get(r[0])
            record(L, f"Table 6.1 {r[0]} · {col}", want == v, f"chapter {v} · data {want}")
    g = {k: got["logistic"][k] for k in got["logistic"]}
    n_t = float(g["Effective treated sample, ATE"].split(" of ")[1].replace(",", ""))
    ess_t = float(g["Effective treated sample, ATE"].split(" of ")[0].replace(",", ""))
    ess_c = float(g["Effective control sample, ATT"].split(" of ")[0].replace(",", ""))
    claim("4,867 treated carry the information of 3,724",
          "4,867 treated persons carry the information of 3,724", ess_t,
          ok=(n_t, ess_t) == (4867, 3724))
    claim("controls carry the information of about 25,000",
          "carry the information of about 25,000", ess_c, ok=abs(ess_c - 25000) < 500)
    claim("the largest ATE weight is 36.8", "The largest ATE weight is 36.8",
          float(g["Largest ATE weight"]), "36.8")
    claim("stabilised: from 36.8 to 4.2", "falls from 36.8 to 4.2",
          float(g["Largest stabilised ATE weight"]), "4.2")
    top = float(g["Heaviest 1% of controls, ATT"].split("%")[0])
    claim("heaviest one per cent carry under five per cent",
          "carry under five per cent of the total control weight", top, ok=top < 5)

    # -- Script 6.2's draws --------------------------------------------------
    f = results / "weighting_results.csv"
    record(L, "Script 6.2 results present", f.exists(),
           "" if f.exists() else f"run ch06/06_02_compare_weighting.py first ({results})")
    if f.exists():
        t = pd.read_csv(f)
        ok = t.seed.nunique() == 6
        record(L, "Script 6.2 results cover six draws", ok,
               f"{t.seed.nunique()} draw(s); --quick output cannot be audited")
        if ok:
            c = lambda *a: s62.cell(t, *a)                              # noqa: E731

            # Table 6.2
            _, rows, cap = ms_table(s, "6.2")
            est = {"Unnormalised (Horvitz–Thompson)": "unnormalised",
                   "Normalised": "normalised", "Normalised, stabilised weights": "stabilised"}
            cols = [("logit", False), ("gbm", False), ("logit", True), ("gbm", True)]
            for r in rows:
                for (sc, tr), v in zip(cols, r[1:]):
                    cell_(f"Table 6.2 {r[0]} · {sc}{' trimmed' if tr else ''}",
                          c(sc, tr, "ATE", est[r[0]])[0], v)
            nrm = t[(t.estimand == "ATE") & (t.estimator == "normalised")].est.values
            stb = t[(t.estimand == "ATE") & (t.estimator == "stabilised")].est.values
            gap = float(np.abs(nrm - stb).max())
            claim("stabilised and normalised agree to ten decimal places",
                  "agree to ten decimal places", gap, ok=gap < 5e-11)

            # Table 6.3
            _, rows, cap = ms_table(s, "6.3")
            key = {"Logistic": ("logit", False), "Logistic, trimmed": ("logit", True),
                   "Boosted": ("gbm", False), "Boosted, trimmed": ("gbm", True)}
            for r in rows:
                sc, tr = key[r[0]]
                for lab, estd, estr, v in (("ATE", "ATE", "normalised", r[1]),
                                           ("ATT", "ATT", "odds", r[2])):
                    b, sd = pair(v)
                    got_ = c(sc, tr, estd, estr)
                    cell_(f"Table 6.3 {r[0]} · {lab} bias", got_[0], b)
                    cell_(f"Table 6.3 {r[0]} · {lab} sd", got_[1], sd)
            u = t[(t.score == "logit") & (~t.trimmed) & (t.estimator == "normalised")]
            v_ = t[(t.score == "logit") & (~t.trimmed) & (t.estimator == "odds")]
            claim("true ATE $5,417", "The true ATE is $5,417", u.truth.mean(), "$5,417")
            claim("true ATT $6,446", "the true ATT $6,446", v_.truth.mean(), "$6,446")

            # Table 6.4
            _, rows, _ = ms_table(s, "6.4")
            for r in rows:
                if r[0] == "No cap":
                    a_, b_ = c("logit", False, "ATE", "normalised"), c("logit", False, "ATT", "odds")
                elif r[0].startswith("Sample trimmed"):
                    a_, b_ = c("logit", True, "ATE", "normalised"), c("logit", True, "ATT", "odds")
                else:
                    q = re.search(r"([\d.]+)th", r[0]).group(1)
                    a_, b_ = c("logit", False, "ATE", f"cap {q}"), c("logit", False, "ATT", f"cap {q}")
                cell_(f"Table 6.4 {r[0]} · ATE", a_[0], r[1])
                cell_(f"Table 6.4 {r[0]} · ATT", b_[0], r[2])
            c90 = c("logit", False, "ATE", "cap 90")[0]
            claim("at the 90th percentile it has the wrong sign",
                  "at the 90th percentile it has the wrong sign", c90, ok=c90 < -100)
            g95 = c("gbm", False, "ATE", "cap 95")[0]
            claim("on the boosted score the 95th-percentile cap reverses the sign",
                  "on the boosted score it reverses the sign", g95, ok=g95 < -100)

            # Table 6.5
            _, rows, _ = ms_table(s, "6.5")
            key = {"Weighting alone": ("logit", False, "normalised", "odds"),
                   "Weighting alone, trimmed": ("logit", True, "normalised", "odds"),
                   "Outcome regression alone": ("logit", False, "regression", "regression"),
                   "Outcome regression alone, trimmed": ("logit", True, "regression", "regression"),
                   "Doubly robust": ("logit", False, "doubly robust", "doubly robust"),
                   "Doubly robust, trimmed": ("logit", True, "doubly robust", "doubly robust"),
                   "Doubly robust, boosted score": ("gbm", False, "doubly robust", "doubly robust"),
                   "Doubly robust, boosted score, trimmed": ("gbm", True, "doubly robust",
                                                             "doubly robust")}
            for r in rows:
                sc, tr, ea, eb = key[r[0]]
                a_, b_ = c(sc, tr, "ATE", ea), c(sc, tr, "ATT", eb)
                cell_(f"Table 6.5 {r[0]} · ATE bias", a_[0], r[1])
                cell_(f"Table 6.5 {r[0]} · ATE sd", a_[1], r[2])
                cell_(f"Table 6.5 {r[0]} · ATT bias", b_[0], r[3])
                cell_(f"Table 6.5 {r[0]} · ATT sd", b_[1], r[4])

            # Section 6.8.3: occupation_group
            for est_, shown in (("ATE", "0.992"), ("ATT", "0.993")):
                a_ = t[(t.score == "logit") & (~t.trimmed) & (t.estimand == est_)
                       & (t.estimator == "doubly robust")].set_index("seed").se
                b_ = t[(t.score == "logit") & (~t.trimmed) & (t.estimand == est_)
                       & (t.estimator == "doubly robust no occupation")].set_index("seed").se
                r_ = a_ / b_
                claim(f"occupation_group: standard error ratio {shown} ({est_})",
                      f"by {shown}" if est_ == "ATT" else f"by a ratio of {shown}",
                      r_.mean(), shown)
                record(L, f"occupation_group: smaller in all six draws ({est_})",
                       bool((r_ < 1).all()), f"{int((r_ < 1).sum())} of {len(r_)}")

            # Table 6.6, and Section 5.12's promise
            _, rows, _ = ms_table(s, "6.6")
            key = {"Odds weighting": "odds", "Doubly robust": "doubly robust",
                   "Propensity score matching (Chapter 5)": "PS matching",
                   "Propensity score matching with regression adjustment":
                       "PS matching + regression",
                   "Mahalanobis matching within a caliper (Chapter 5)": "Mahalanobis matching"}
            for r in rows:
                got_ = c("logit", False, "ATT", key[r[0]])
                cell_(f"Table 6.6 {r[0]} · bias", got_[0], r[1])
                cell_(f"Table 6.6 {r[0]} · sd", got_[1], r[2])
            dr = abs(c("logit", False, "ATT", "doubly robust")[0])
            record(L, "Section 5.12: doubly robust beats matched regression, not odds or Mahalanobis",
                   dr < abs(c("logit", False, "ATT", "PS matching + regression")[0])
                   and dr > abs(c("logit", False, "ATT", "odds")[0])
                   and dr > abs(c("logit", False, "ATT", "Mahalanobis matching")[0]),
                   f"|DR| {dr:.1f}")

            # Section 6.7: the near-instrument
            w0 = t[(t.score == "logit") & (~t.trimmed) & (t.estimand == "diag")]
            w1 = t[(t.score == "logit+mo") & (t.estimand == "diag")]
            b0, b1 = c("logit", False, "ATT", "odds"), c("logit+mo", False, "ATT", "odds")
            claim("largest odds weight 1.5", "from 1.5 to 21.7", w0.max_odds.mean(), "1.5")
            claim("... to 21.7", "from 1.5 to 21.7", w1.max_odds.mean(), "21.7")
            claim("effective control sample 24,271", "from 24,271 to 3,458",
                  w0.ess_att_c.mean(), "24,271")
            claim("... to 3,458", "from 24,271 to 3,458", w1.ess_att_c.mean(), "3,458")
            claim("six sevenths of the control information", "six sevenths of the control information",
                  1 - w1.ess_att_c.mean() / w0.ess_att_c.mean(),
                  ok=abs((1 - w1.ess_att_c.mean() / w0.ess_att_c.mean()) - 6 / 7) < 0.02)
            claim("near-instrument ATT bias -8.8", f"from {M}11.8 to {M}8.8 per cent", b1[0], "-8.8")
            claim("sd from 5.4 to 9.3", "from 5.4 to 9.3", b1[1], "9.3")
            claim("naive se from 367 to 479", "from 367 to 479", b1[3], "479")

            # Section 6.9 and Table 6.8
            four = [c("logit", False, "ATT", e)[0] for e in
                    ("odds", "doubly robust", "PS matching", "PS matching + regression")]
            claim("cluster between -11.8 and -15.4", f"between {M}11.8 and {M}15.4 per cent",
                  max(four), ok=_agrees(max(four), "-11.8") and _agrees(min(four), "-15.4"))
            _, rows, _ = ms_table(s, "6.8")
            key = {"Normalised IPW, ATE": ("ATE", "normalised"), "Odds weighting, ATT": ("ATT", "odds"),
                   "Doubly robust, ATE": ("ATE", "doubly robust"),
                   "Doubly robust, ATT": ("ATT", "doubly robust")}
            for r in rows:
                got_ = c("logit", False, *key[r[0]])
                cell_(f"Table 6.8 {r[0]} · naive SE", got_[3], r[1])
                cell_(f"Table 6.8 {r[0]} · spread", got_[2], r[2])
                cell_(f"Table 6.8 {r[0]} · ratio", got_[3] / got_[2], r[3])

            # Section 6.11.2: the accounting
            L0 = c("logit", False, "ATE", "normalised")[0]
            acct = [
                ("capping at 95th cost 77 points", "cost 77 percentage points",
                 c("logit", False, "ATE", "cap 95")[0] - L0, "-77"),
                ("trimming worth 11 (logistic)", "worth 11 percentage points on the logistic score",
                 abs(L0) - abs(c("logit", True, "ATE", "normalised")[0]), "11"),
                ("trimming worth 29 (boosted)", "and 29 on the boosted score",
                 abs(c("gbm", False, "ATE", "normalised")[0])
                 - abs(c("gbm", True, "ATE", "normalised")[0]), "29"),
                ("normalisation worth 3 (logistic)", "Normalisation was worth 3",
                 abs(c("logit", False, "ATE", "unnormalised")[0]) - abs(L0), "3"),
                ("normalisation worth 58 (boosted)", "and 58 on the boosted",
                 abs(c("gbm", False, "ATE", "unnormalised")[0])
                 - abs(c("gbm", False, "ATE", "normalised")[0]), "58"),
                ("doubly robust worth 6 on the ATE", "worth 6 on the ATE",
                 abs(L0) - abs(c("logit", False, "ATE", "doubly robust")[0]), "6"),
            ]
            for lab, snip, val, shown in acct:
                claim(lab, snip, val, shown)
            nothing = abs(c("logit", False, "ATT", "doubly robust")[0]) >= \
                abs(c("logit", False, "ATT", "odds")[0])
            claim("doubly robust worth nothing on the ATT", "and nothing on the ATT", 0.0, ok=nothing)

    # -- Table 6.7: Script 6.3's draws ----------------------------------------
    f7 = results / "wrong_reason_results.csv"
    record(L, "Script 6.3 results present", f7.exists(),
           "" if f7.exists() else f"run ch06/06_03_right_for_the_wrong_reason.py first ({results})")
    if f7.exists():
        w = pd.read_csv(f7)
        ok = len(w) == 6
        record(L, "Script 6.3 results cover six draws", ok, f"{len(w)} draw(s)")
        if ok:
            m, sd = w.mean(), w.std()
            _, rows, cap = ms_table(s, "6.7")
            key = {"Odds weighting, Chapter 3's propensity score": "odds_reader",
                   "Odds weighting, the true propensity score": "odds_true",
                   "Odds weighting, both unobserved confounders added": "odds_hidden",
                   "Outcome regression, the observed covariates": "reg_reader",
                   "Outcome regression, both unobserved confounders added": "reg_hidden"}
            for r in rows:
                cell_(f"Table 6.7 {r[0]} · bias", m[key[r[0]]], r[1])
                cell_(f"Table 6.7 {r[0]} · sd", sd[key[r[0]]], r[2])
            claim("Chapter 3's score correlates with the true score at 0.44",
                  "correlates with the true score at only 0.44", m.corr_true, "0.44")
            claim("true-score weighting +0.4 with sd 11.6", "standard deviation of 11.6",
                  sd.odds_true, "11.6")
            claim("hidden confounders: -11.8 to -7.6", f"from {M}11.8 to {M}7.6 per cent",
                  m.odds_hidden, "-7.6")
            claim("regression: +0.5 to +5.4", "from +0.5 to +5.4 per cent", m.reg_hidden, "+5.4")


# ===========================================================================

def layer_e5_ch9(s: str, repo: Path) -> None:
    """Chapter 5 v1.7: the claims about reuse and the recommended design rest on Chapter 9."""
    L = "E chapter 5"
    prose = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)
    t = ch9_committed(repo)
    record(L, "Chapter 9's committed run present", t is not None)
    if t is None:
        return
    w = t.pivot(index="seed", columns="estimator", values="bias")
    rm = {k: np.sqrt((w[k] ** 2).mean()) for k in ("maha", "maha13")}
    snip = "reduce the draw-to-draw standard deviation from 5.4 to 4.1 points and cost about two points of bias (\u22123.3 against \u22121.3 per cent)"
    ok = (snip in prose and _agrees(w["maha"].std(), "5.4") and _agrees(w["maha13"].std(), "4.1")
          and _agrees(w["maha13"].mean(), "-3.3") and _agrees(w["maha"].mean(), "-1.3")
          and rm["maha13"] < rm["maha"])
    record(L, "claim: Section 5.16.3's design, measured in Chapter 9", ok,
           f"sd {w['maha'].std():.2f} to {w['maha13'].std():.2f}; bias {w['maha'].mean():.2f} to {w['maha13'].mean():.2f}")
    record(L, "Section 5.16.3 no longer claims the smallest bias and variability",
           "gives the smallest bias, the smallest draw-to-draw variability" not in prose)
    sp = t.assign(err=t.est - t.truth).groupby("estimator").err.std()
    q = t[t.estimator == "match_repl"]
    extra = q.se_ai.mean() / q.se_paired.mean() - 1
    record(L, "claim: reuse adds only a few per cent to the standard error",
           "the reuse adds only a few per cent to the standard error" in prose and 0 < extra < 0.1,
           f"{100 * extra:.1f}%")
    record(L, "Section 5.3.3 no longer says the naive SE will be too small",
           "any standard error computed as though they were will be too small" not in prose)


def layer_e6_ch9(s: str, repo: Path) -> None:
    """Chapter 6 v1.1: Section 6.10 now defers to Chapter 9's 200 draws."""
    L = "E chapter 6"
    t = ch9_committed(repo)
    record(L, "Chapter 9's committed run present", t is not None)
    if t is None:
        return
    sp = t.assign(err=t.est - t.truth).groupby("estimator").err.std()
    r = lambda k: t[t.estimator == k].se_naive.mean() / sp[k]              # noqa: E731
    _, rows, _ = ms_table(s, "6.8")
    ratios = [float(x[3]) for x in rows]
    record(L, "claim: Table 6.8's ratios run from 0.72 to 1.21",
           "run from 0.72 to 1.21" in s and min(ratios) == 0.72 and max(ratios) == 1.21, f"{ratios}")
    record(L, "claim: 200 draws: conservative by about half (odds) and a fifth (ATE)",
           "by about half for odds weighting and a fifth for the normalised ATE" in s
           and 1.4 < r("odds") < 1.6 and 1.15 < r("ipw_ate") < 1.25, f"{r('odds'):.2f}, {r('ipw_ate'):.2f}")
    record(L, "claim: doubly robust close to right", "The doubly robust standard errors are close to right" in s
           and abs(r("dr_att") - 1) < 0.1 and abs(r("dr_ate") - 1) < 0.1, f"{r('dr_att'):.2f}, {r('dr_ate'):.2f}")
    record(L, "Section 6.10 no longer says the DR ATT understates by a quarter",
           "understates the actual spread by more than a quarter" not in s)


def layer_e7(s: str, repo: Path, data: Path, results: Path) -> None:
    L = "E chapter 7"
    prose = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)
    words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}

    def cell_(check, got, shown):
        record(L, check, _agrees(got, shown), f"chapter {shown} · data {got:,.4f}")

    def claim(label, snippet, got, shown=None, ok=None):
        if snippet.lower() not in prose.lower():
            record(L, f"claim: {label}", False, f"text not found: '{snippet}'")
            return
        ok = _agrees(got, shown) if ok is None else ok
        det = (f"chapter {shown} · data {got:,.4f}" if shown is not None
               else f"data {got:,.4f}" if isinstance(got, (int, float)) else str(got))
        record(L, f"claim: {label}", bool(ok), det)

    def pair(text):
        m = re.match(r"([+−-]?[\d.]+)%\s*\(([\d.]+)\)", text)
        return (m.group(1), m.group(2)) if m else (text.replace("%", ""), None)

    if not (data / "analysis_file.csv").exists():
        for scr in ("ch02/02_05_link_modules.py", "ch02/02_06_reshape_panel.py"):
            subprocess.run([sys.executable, str(repo / scr), "--datadir", str(data)],
                           check=True, capture_output=True)
    s71 = _load_script(repo / "ch07" / "07_01_form_strata.py", "s71")
    s72 = _load_script(repo / "ch07" / "07_02_compare_strata.py", "s72")
    sc = s71.score(data, "logit", with_truth=True)
    D, ps, y, tau = sc["D"], sc["ps"], sc["y"], sc["tau"]

    # -- Table 7.1: the identity, on the primary dataset -----------------------
    got = {r[0]: r for r in s71.table_7_1(ps, D, y)}
    _, rows, _ = ms_table(s, "7.1")
    for r in rows:
        g = got.get(r[0])
        if g is None:
            record(L, f"Table 7.1 row {r[0]} in data", False)
            continue
        if r[1]:
            cell_(f"Table 7.1 {r[0]} · subclassification", g[1], r[1])
        cell_(f"Table 7.1 {r[0]} · weighted", g[2], r[2])
        if r[3]:
            record(L, f"Table 7.1 {r[0]} · difference is rounding error",
                   g[3] < 1e-8 and _num(r[3].replace("e−", "e-")) < 1e-8,
                   f"chapter {r[3]} · data {g[3]:.1e}")
        cell_(f"Table 7.1 {r[0]} · effective controls", g[4], r[4])
    n_c = int((D == 0).sum())
    claim("37,708 controls carry the information of about 27,600",
          f"the {n_c:,} controls carry the information of about 27,600",
          got["5 strata"][4], ok=abs(got["5 strata"][4] - 27600) < 100)
    claim("100 strata fall slightly below the odds weights' 25,057",
          "at 100 strata slightly below, the 25,057",
          got["100 strata"][4], ok=got["100 strata"][4] < got["Odds weighting (Chapter 6)"][4]
          and _agrees(got["Odds weighting (Chapter 6)"][4], "25,057"))

    # -- Table 7.2 ---------------------------------------------------------------
    t72 = s71.table_7_2(ps, D, y, tau)
    _, rows, _ = ms_table(s, "7.2")
    record(L, "Table 7.2 has five strata", len(rows) == len(t72) == 5)
    for r, g in zip(rows, t72):
        lo, hi = r[1].split(" to ")
        cell_(f"Table 7.2 stratum {r[0]} · lower score", g["lo"], lo)
        cell_(f"Table 7.2 stratum {r[0]} · upper score", g["hi"], hi)
        for i, k in ((2, "n_t"), (3, "n_c"), (4, "y_t"), (5, "y_c"), (6, "diff"),
                     (7, "share"), (8, "true_att")):
            cell_(f"Table 7.2 stratum {r[0]} · {k}", g[k], r[i])
    est = sum(g["diff"] * g["share"] for g in t72)
    truth = tau[D == 1].mean()
    naive = y[D == 1].mean() - y[D == 0].mean()
    claim("ATT of $5,053", "give an ATT of $5,053", est, "5,053")
    claim("true value of $6,408", "against a true value of $6,408", truth, "6,408")
    claim("bias of −21.2 per cent", "a bias of −21.2 per cent", 100 * (est - truth) / truth, "−21.2")
    claim("naive −$2,910", "−$2,910", naive, "−2,910")
    claim("naive −145.4 per cent", "a bias of −145.4 per cent", 100 * (naive - truth) / truth, "−145.4")
    claim("highest stratum holds 1,847 treated", "the highest stratum holds 1,847", t72[4]["n_t"], "1,847")
    claim("38 per cent of the weight", "therefore 38 per cent of the weight", 100 * t72[4]["share"], "38")
    claim("lowest holds 387", "while the lowest holds 387", t72[0]["n_t"], "387")
    claim("each stratum about 8,500", "the same number of persons, about 8,500",
          (t72[0]["n_t"] + t72[0]["n_c"]), ok=abs(t72[0]["n_t"] + t72[0]["n_c"] - 8500) < 100)
    claim("stratum 5 difference $6,622 against $7,809",
          "The difference in stratum 5 is $6,622 against a true effect of $7,809",
          t72[4]["diff"], ok=_agrees(t72[4]["diff"], "6,622") and _agrees(t72[4]["true_att"], "7,809"))
    claim("stratum 1 difference negative where the truth is positive",
          "the difference in stratum 1 is negative where the true effect is positive",
          t72[0]["diff"], ok=t72[0]["diff"] < 0 < t72[0]["true_att"])

    top = s71.strata(ps, D, 5) == 4
    inc = sc["X"]["log_inc_2016"]
    ratio = inc[top].std() / inc.std()
    claim("prior income varies almost as widely within the highest stratum",
          "varies almost as widely within the highest stratum as in the whole population",
          ratio, ok=ratio > 0.9)

    # -- In the DataLab: cell sizes ------------------------------------------
    sm = {K: s71.cell_sizes(ps, D, K) for K in (5, 20, 100, 200)}
    claim("five strata: smallest cell 387", "With five strata on the primary dataset the smallest cell holds 387",
          sm[5][0], "387")
    claim("100 strata: smallest cell 11", "With 100 strata it holds 11", sm[100][0], "11")
    claim("100 strata: 12 of 200 cells under 20", "12 of the 200 cells hold fewer than 20", sm[100][1], "12")
    claim("200 strata: smallest 3", "with 200 strata the smallest holds 3", sm[200][0], "3")
    claim("200 strata: 93 cells under 20", "93 cells fall below 20", sm[200][1], "93")
    claim("twenty strata: smallest cell 68", "the smallest cell holds 68 persons", sm[20][0], "68")

    # -- Script 7.2's draws ----------------------------------------------------
    f = results / "strata_results.csv"
    record(L, "Script 7.2 results present", f.exists(),
           "" if f.exists() else f"run ch07/07_02_compare_strata.py first ({results})")
    t = pd.read_csv(f) if f.exists() else None
    ok6 = t is not None and t.seed.nunique() == 6
    if t is not None:
        record(L, "Script 7.2 results cover six draws", ok6,
               f"{t.seed.nunique()} draw(s); --quick output cannot be audited")
    if ok6:
        c = lambda *a, **k: s72.cell(t, *a, **k)                         # noqa: E731

        # Table 7.3
        _, rows, _ = ms_table(s, "7.3")
        spec = {"Odds weighting (ATT)": ("odds weighting", None),
                "Normalised IPW (ATE)": ("normalised IPW", None),
                "Naive difference in means": ("naive", None)}
        for r in rows:
            est, K = spec.get(r[0], ("subclassification", int(r[0].split()[0])
                                     if r[0].split()[0].isdigit() else None))
            for col, estimand, trimmed in ((1, "ATT", False), (2, "ATT", True),
                                           (3, "ATE", False), (4, "ATE", True)):
                if not r[col]:
                    continue
                m, sd = c(trimmed, estimand, est, K)
                b, sd_shown = pair(r[col])
                cell_(f"Table 7.3 {r[0]} · {estimand}{' trimmed' if trimmed else ''}", m, b)
                if sd_shown:
                    cell_(f"Table 7.3 {r[0]} · {estimand} sd", sd, sd_shown)

        sub = t[(t.estimator == "subclassification") & (~t.trimmed)]
        w = {e: sub[sub.estimand == e].pivot(index="seed", columns="K", values="bias")
             for e in ("ATT", "ATE")}
        d = w["ATT"][20] - w["ATT"][5]
        de = w["ATE"][20] - w["ATE"][5]
        claim("five to twenty: between 9.0 and 11.6 in every draw",
              "by between 9.0 and 11.6 percentage points in every draw",
              d.min(), ok=_agrees(d.min(), "9.0") and _agrees(d.max(), "11.6") and (d > 0).all())
        claim("five to twenty: 10.2 on average", "by 10.2 on average", d.mean(), "10.2")
        claim("... with a standard deviation of only 1.10", "standard deviation of only 1.10", d.std(), "1.10")
        claim("draw sd with twenty strata 5.5", "which is 5.5 with twenty strata", w["ATT"][20].std(), "5.5")
        claim("twenty to 100: ATT 1.4", "improves the ATT by a further 1.4",
              (w["ATT"][100] - w["ATT"][20]).mean(), "1.4")
        claim("twenty to 100: ATE 1.6", "and the ATE by 1.6", (w["ATE"][100] - w["ATE"][20]).mean(), "1.6")
        claim("ATE twenty strata −17.8 against −22.7", "at −17.8 per cent against −22.7",
              c(False, "ATE", "subclassification", 20)[0],
              ok=_agrees(c(False, "ATE", "subclassification", 20)[0], "−17.8")
              and _agrees(c(False, "ATE", "normalised IPW")[0], "−22.7"))
        claim("... and somewhat more stable", "and somewhat more stable",
              c(False, "ATE", "subclassification", 20)[1],
              ok=c(False, "ATE", "subclassification", 20)[1] < c(False, "ATE", "normalised IPW")[1])
        for e, pct_, shown in (("ATT", 85, "85"), ("ATE", 80, "80")):
            nv = t[(t.estimator == "naive") & (~t.trimmed) & (t.estimand == e)].set_index("seed").bias
            ref = t[(t.estimator == ("odds weighting" if e == "ATT" else "normalised IPW"))
                    & (~t.trimmed) & (t.estimand == e)].set_index("seed").bias
            rem = 100 * (1 - (w[e][5] / nv)).mean()
            rel = 100 * ((nv - w[e][5]) / (nv - ref)).mean()
            claim(f"five strata remove {shown}% of the naive {e} bias",
                  "Five strata remove 85 per cent of the naive bias in the ATT and 80 per cent in the ATE",
                  rem, shown)
            claim(f"five strata achieve {'92' if e == 'ATT' else '94'}% of weighting's reduction, {e}",
                  "achieve 92 per cent of it for the ATT and 94 per cent for the ATE",
                  rel, "92" if e == "ATT" else "94")
        tq5 = c(False, "ATT", "subclassification, treated quantiles", 5)[0]
        tq20 = c(False, "ATT", "subclassification, treated quantiles", 20)[0]
        claim("treated quantiles: −26.5 against −22.2", "a bias of −26.5 per cent across the six draws, against −22.2",
              tq5, ok=_agrees(tq5, "−26.5") and _agrees(c(False, "ATT", "subclassification", 5)[0], "−22.2"))
        claim("treated quantiles: similar at twenty", "and similarly at twenty",
              tq20, ok=abs(tq20 - c(False, "ATT", "subclassification", 20)[0]) < 2)
        claim("no stratum ever dropped", "this never happened, at any number of strata up to 100",
              t.dropped.max(), ok=t.dropped.max() == 0)
        rs = []
        for tr in (False, True):
            for e in ("ATT", "ATE"):
                for K in (5, 10, 20):
                    q = t[(t.estimator == "subclassification") & (t.trimmed == tr)
                          & (t.estimand == e) & (t.K == K)]
                    rs.append(q.se.mean() / (q.est - q.truth).std())
        claim("standard error ratio 0.71 to 1.27", "ranged from 0.71 to 1.27 times",
              min(rs), ok=_agrees(min(rs), "0.71") and _agrees(max(rs), "1.27"))

        # Table 7.4
        _, rows, _ = ms_table(s, "7.4")
        for r in rows:
            K = int(r[0].split()[0])
            for j, e in ((1, "ATT"), (4, "ATE")):
                cell_(f"Table 7.4 {K} strata · {e} largest SMD", c(False, e, "balance", K, "max_smd")[0], r[j])
                cell_(f"Table 7.4 {K} strata · {e} over 0.1", c(False, e, "balance", K, "over_01")[0], r[j + 1])
                cell_(f"Table 7.4 {K} strata · {e} bias", c(False, e, "subclassification", K)[0],
                      r[j + 2].replace("%", ""))
        claim("ATE five strata: largest 0.054, every covariate passes",
              "every covariate passes the threshold at five strata, with the largest standardised difference at 0.054",
              c(False, "ATE", "balance", 5, "max_smd")[0],
              ok=_agrees(c(False, "ATE", "balance", 5, "max_smd")[0], "0.054")
              and t[(t.estimator == "balance") & (t.estimand == "ATE") & (t.K == 5) & (~t.trimmed)].over_01.max() == 0)
        claim("... while biased by −31.5", "while the estimate is biased by −31.5 per cent",
              c(False, "ATE", "subclassification", 5)[0], "−31.5")
        claim("ATT ten strata: none over 0.1 while 14.8 per cent low", "still 14.8 per cent low",
              c(False, "ATT", "subclassification", 10)[0],
              ok=_agrees(-c(False, "ATT", "subclassification", 10)[0], "14.8")
              and t[(t.estimator == "balance") & (t.estimand == "ATT") & (t.K == 10) & (~t.trimmed)].over_01.max() == 0)

        # Table 7.5
        _, rows, _ = ms_table(s, "7.5")
        for r in rows:
            K = int(r[0].split()[0])
            for col, e, tr in ((1, "ATT", False), (2, "ATT", True), (3, "ATE", False), (4, "ATE", True)):
                m, sd = c(tr, e, "subclassification + regression", K)
                b, sd_shown = pair(r[col])
                cell_(f"Table 7.5 {K} strata · {e}{' trimmed' if tr else ''}", m, b)
                if sd_shown:
                    cell_(f"Table 7.5 {K} strata · {e} sd", sd, sd_shown)
            cell_(f"Table 7.5 {K} strata · without regression", c(False, "ATT", "subclassification", K)[0],
                  r[5].replace("%", ""))
        rr = t[(t.estimator == "subclassification + regression") & (~t.trimmed)]
        wr = {e: rr[rr.estimand == e].pivot(index="seed", columns="K", values="bias") for e in ("ATT", "ATE")}
        spread = (wr["ATT"].max(axis=1) - wr["ATT"].min(axis=1)).mean()
        claim("regression: −9.4, −9.3 and −9.0", "the ATT is −9.4, −9.3 and −9.0 per cent",
              wr["ATT"][5].mean(), ok=all(_agrees(wr["ATT"][K].mean(), v)
                                          for K, v in ((5, "−9.4"), (10, "−9.3"), (20, "−9.0"))))
        claim("within-draw spread 0.66", "an average of only 0.66 percentage points", spread, "0.66")
        claim("ATE about −8.5 untrimmed", "at about −8.5 per cent untrimmed",
              wr["ATE"].mean().mean(), ok=all(abs(wr["ATE"][K].mean() + 8.5) < 0.2 for K in (5, 10, 20)))

        # Section 7.7's box
        q = t[(t.estimator == "regression on the score") & (~t.trimmed)]
        qt = t[(t.estimator == "regression on the score") & (t.trimmed)]
        by = lambda d_, e, col: d_[d_.estimand == e][col].mean()        # noqa: E731
        claim("regression on the score averages $5,423", "averages $5,423 across the six draws",
              q[q.estimand == "ATE"].est.mean(), "5,423")
        claim("true ATE $5,417", "against a true ATE of $5,417", by(q, "ATE", "truth"), "5,417")
        claim("bias +0.1 per cent", "a bias of +0.1 per cent", by(q, "ATE", "bias"), "0.1")
        claim("overlap effect $6,147", "it averages $6,147 across the six draws", by(q, "ATO", "truth"), "6,147")
        claim("box repeats ATE $5,417 and ATT $6,446", "between the ATE of $5,417 and the ATT of $6,446",
              by(q, "ATT", "truth"), ok=_agrees(by(q, "ATT", "truth"), "6,446")
              and _agrees(by(q, "ATE", "truth"), "5,417"))
        claim("against its own estimand 11.8 per cent low", "the regression is 11.8 per cent low",
              -by(q, "ATO", "bias"), "11.8")
        claim("overlap weighting −10.8", "gives −10.8 per cent",
              c(False, "ATO", "overlap weighting")[0], "−10.8")
        claim("trimmed: +1.2 against the ATE", "the bias against the ATE is +1.2 per cent",
              by(qt, "ATE", "bias"), "1.2")

        # Section 7.8
        claim("trimming: ATE −31.5 to −19.2 at five strata", "the ATE moves from −31.5 to −19.2 per cent",
              c(True, "ATE", "subclassification", 5)[0], ok=_agrees(c(True, "ATE", "subclassification", 5)[0], "−19.2"))
        claim("trimming: ATT −22.2 to −18.0", "the ATT from −22.2 to −18.0",
              c(True, "ATT", "subclassification", 5)[0], "−18.0")
        claim("trimmed ATT at twenty −10.6 against odds −8.6", "at −10.6 per cent, is close to the trimmed odds weighting estimate of −8.6",
              c(True, "ATT", "subclassification", 20)[0],
              ok=_agrees(c(True, "ATT", "subclassification", 20)[0], "−10.6")
              and _agrees(c(True, "ATT", "odds weighting")[0], "−8.6"))

        # Table 7.8
        _, rows, _ = ms_table(s, "7.8")
        spec8 = {"Propensity score matching, caliper 0.1 (Chapter 5)": ("PS matching", None),
                 "Mahalanobis matching within a caliper (Chapter 5)": ("Mahalanobis matching", None),
                 "Odds weighting (Chapter 6)": ("odds weighting", None),
                 "Doubly robust (Chapter 6)": ("doubly robust", None),
                 "Subclassification, 20 strata": ("subclassification", 20),
                 "Subclassification, 20 strata, regression within strata": ("subclassification + regression", 20),
                 "Outcome modelled on the score, with covariates": ("spline on the score + covariates", None)}
        sds = []
        for r in rows:
            est, K = spec8.get(r[0], (None, None))
            if est is None:
                record(L, f"Table 7.8 row {r[0]} known", False)
                continue
            if "matching" in est:
                m, sd = s72.matched_bias(t, False, est)
                mt_, _ = s72.matched_bias(t, True, est)
            else:
                m, sd = c(False, "ATT", est, K)
                mt_, _ = c(True, "ATT", est, K)
            b, sd_shown = pair(r[1])
            cell_(f"Table 7.8 {r[0]} · untrimmed", m, b)
            cell_(f"Table 7.8 {r[0]} · sd", sd, sd_shown)
            cell_(f"Table 7.8 {r[0]} · trimmed", mt_, r[2].replace("%", ""))
            if "matching" not in est:
                sds.append(sd)
        claim("score-based estimators' sd between 5.4 and 6.0", "between 5.4 and 6.0",
              min(sds), ok=_agrees(min(sds), "5.4") and _agrees(max(sds), "6.0"))

        # Section 7.11.2
        att = lambda K, e="ATT", est="subclassification", tr=False: c(tr, e, est, K)[0]  # noqa: E731
        claim("cost: five to twenty 10.2 ATT and 13.7 ATE", "was worth 10.2 percentage points on the ATT and 13.7 on the ATE",
              de.mean(), ok=_agrees(d.mean(), "10.2") and _agrees(de.mean(), "13.7"))
        claim("cost: twenty to 100 worth 1.4 and 1.6", "was worth a further 1.4 and 1.6",
              (w["ATT"][100] - w["ATT"][20]).mean(), "1.4")
        claim("cost: regression worth 12.8 at five and 3.0 at twenty",
              "worth 12.8 points on the ATT at five strata and 2.9 at twenty",
              att(5, est="subclassification + regression") - att(5),
              ok=_agrees(att(5, est="subclassification + regression") - att(5), "12.8")
              and _agrees(att(20, est="subclassification + regression") - att(20), "2.9"))
        claim("cost: trimming worth 4.2 at five and 1.4 at twenty",
              "Trimming was worth 4.2 points on the ATT at five strata and 1.3 at twenty",
              att(5, tr=True) - att(5), ok=_agrees(att(5, tr=True) - att(5), "4.2")
              and _agrees(att(20, tr=True) - att(20), "1.3"))

    # -- Script 7.3's draws ----------------------------------------------------
    f, f2 = results / "spline_results.csv", results / "spline_thinnest.csv"
    have = f.exists() and f2.exists()
    record(L, "Script 7.3 results present", have,
           "" if have else f"run ch07/07_03_spline_on_score.py first ({results})")
    if have:
        sp, th = pd.read_csv(f), pd.read_csv(f2)
        ok = sp.seed.nunique() == 6 and len(th) == 6
        record(L, "Script 7.3 results cover six draws", ok, f"{sp.seed.nunique()} draw(s)")
        if ok:
            def spc(knots, cov, e, tr):
                q = sp[(sp.knots == knots) & (sp.covariates == cov) & (sp.estimand == e)
                       & (sp.trimmed == tr)]
                return q.bias.mean(), q.bias.std()
            _, rows, _ = ms_table(s, "7.6")
            for r in rows:
                knots = "quantile" if "quantiles" in r[0] else "uniform"
                cov = "covariates" in r[0]
                for col, e, tr in ((1, "ATT", False), (2, "ATT", True), (3, "ATE", False), (4, "ATE", True)):
                    m, sd = spc(knots, cov, e, tr)
                    b, sd_shown = pair(r[col])
                    cell_(f"Table 7.6 {r[0]} · {e}{' trimmed' if tr else ''}", m, b)
                    if sd_shown:
                        cell_(f"Table 7.6 {r[0]} · {e} sd", sd, sd_shown)
            claim("quantile knots: ATT −10.2 and −11.5", "the ATT is −10.2 per cent without covariates and −11.5 per cent with them",
                  spc("quantile", False, "ATT", False)[0],
                  ok=_agrees(spc("quantile", False, "ATT", False)[0], "−10.2")
                  and _agrees(spc("quantile", True, "ATT", False)[0], "−11.5"))
            claim("quantile knots: ATE −16.4 and −13.9", "the ATE is −16.4 and −13.9 per cent",
                  spc("quantile", False, "ATE", False)[0],
                  ok=_agrees(spc("quantile", False, "ATE", False)[0], "−16.4")
                  and _agrees(spc("quantile", True, "ATE", False)[0], "−13.9"))
            claim("trimmed ATE about −11.5", "improving to about −11.5 per cent after trimming",
                  spc("quantile", False, "ATE", True)[0],
                  ok=all(abs(spc("quantile", cv, "ATE", True)[0] + 11.5) < 0.3 for cv in (False, True)))
            ua, ue = spc("uniform", False, "ATT", False)[0], spc("uniform", False, "ATE", False)[0]
            claim("evenly spaced: ATT out by more than a thousand per cent", "the ATT is out by more than a thousand per cent",
                  ua, ok=abs(ua) > 1000)
            claim("... and the ATE by nearly two hundred", "and the ATE by nearly two hundred",
                  ue, ok=150 < abs(ue) < 200)
            u = sp[(sp.knots == "uniform") & (~sp.covariates) & (~sp.trimmed)].pivot(
                index="seed", columns="estimand", values="bias")
            calm = int(((u.abs() < 20).all(axis=1)).sum())
            claim("three of six draws unremarkable", f"in {words[calm]} of the six draws the estimates are unremarkable",
                  calm, ok=True)
            claim("thinnest evenly spaced interval: 13 or fewer treated", "holds 13 or fewer treated persons",
                  th.uniform_t.max(), "13")
            claim("one draw: 3 treated and a single control", "in one draw it holds 3 treated persons and a single control",
                  th.uniform_c.min(), ok=((th.uniform_t == 3) & (th.uniform_c == 1)).any())
            claim("quantile knots: at least 156 treated", "the thinnest holds at least 156 treated persons",
                  th.quantile_t.min(), "156")
            _, rows, _ = ms_table(s, "7.7")
            thi = th.set_index("seed")
            for r in rows:
                sd_ = int(r[0])
                if sd_ not in thi.index:
                    record(L, f"Table 7.7 draw {r[0]} in data", False)
                    continue
                for j, k in ((1, "uniform_t"), (2, "uniform_c"), (3, "quantile_t"), (4, "quantile_c")):
                    cell_(f"Table 7.7 {r[0]} · {k}", thi.loc[sd_, k], r[j])
                cell_(f"Table 7.7 {r[0]} · ATT bias", u.loc[sd_, "ATT"], r[5].replace("%", ""))
                cell_(f"Table 7.7 {r[0]} · ATE bias", u.loc[sd_, "ATE"], r[6].replace("%", ""))


def layer_e8(s: str, repo: Path, data: Path, results: Path) -> None:
    L = "E chapter 8"
    prose = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)
    words = {6: "six", 5: "five", 4: "four", 3: "three", 1: "one", 0: "none"}

    def cell_(check, got, shown):
        record(L, check, _agrees(got, shown), f"chapter {shown} · data {got:,.4f}")

    def claim(label, snippet, got, shown=None, ok=None):
        if snippet.lower() not in prose.lower():
            record(L, f"claim: {label}", False, f"text not found: '{snippet}'")
            return
        ok = _agrees(got, shown) if ok is None else ok
        det = (f"chapter {shown} · data {got:,.4f}" if shown is not None
               else f"data {got:,.4f}" if isinstance(got, (int, float, np.floating, np.integer)) else str(got))
        record(L, f"claim: {label}", bool(ok), det)

    def pair(text):
        m = re.match(r"([+−-]?[\d.]+)%\s*\(([\d.]+)\)", text)
        return (m.group(1), m.group(2)) if m else (text.replace("%", ""), None)

    if not (data / "analysis_file.csv").exists():
        for scr in ("ch02/02_05_link_modules.py", "ch02/02_06_reshape_panel.py"):
            subprocess.run([sys.executable, str(repo / scr), "--datadir", str(data)],
                           check=True, capture_output=True)
    s81 = _load_script(repo / "ch08" / "08_01_balance_table.py", "s81")
    s82 = _load_script(repo / "ch08" / "08_02_diagnostics_across_draws.py", "s82")
    sc = s81.score(data, "logit")
    E, X, D, ps = sc["E"], sc["X"], sc["D"], sc["ps"]
    S = s81.adjusted_samples(X, D, ps, strata=(5, 20))
    wt, wc = S["Propensity score matching"]

    # -- Table 8.1 -------------------------------------------------------------
    t1, pairs = s81.table_8_1(X, D, wt, wc)
    lab = {v: k for k, v in s81.LABELS.items()}
    _, rows, cap = ms_table(s, "8.1")
    record(L, "Table 8.1 has one row per covariate", len(rows) == len(t1),
           f"table {len(rows)} · data {len(t1)}")
    for r in rows:
        c = lab.get(r[0])
        if c not in t1.index:
            record(L, f"Table 8.1 row {r[0]} in data", False)
            continue
        g = t1.loc[c]
        for j, k in ((1, "treated"), (2, "control_before"), (3, "smd_before"), (4, "control_after"),
                     (5, "smd_after"), (6, "smd_after_fixed")):
            cell_(f"Table 8.1 {r[0]} · {k}", g[k], r[j])
    n_c = int((D == 0).sum())
    record(L, "Table 8.1 caption counts", f"{int(D.sum()):,} treated persons, {n_c:,} controls and "
           f"{pairs:,} matched pairs" in cap, f"{int(D.sum()):,} / {n_c:,} / {pairs:,}")
    over = int((t1.smd_before.abs() > 0.1).sum())
    claim("13 of 18 exceed 0.1 before", f"{over} of the 18 covariates exceed the 0.1 threshold", over, ok=True)
    top = t1.smd_before.abs().sort_values(ascending=False)
    claim("led by fortnights +0.394 and long-term receipt +0.358",
          "led by fortnights on payment at +0.394 and long-term receipt at +0.358",
          top.iloc[0], ok=list(top.index[:2]) == ["fn_2016", "lts"]
          and _agrees(t1.smd_before["fn_2016"], "0.394") and _agrees(t1.smd_before["lts"], "0.358"))
    worst = t1.smd_after_fixed.abs()
    claim("after: largest 0.022, earnings drop", "the largest standardised difference is 0.022, for the earnings drop of 2016",
          worst.max(), ok=_agrees(worst.max(), "0.022") and worst.idxmax() == "drop_2016"
          and int((t1.smd_after.abs() > 0.1).sum()) == 0)
    gap = (t1.smd_after - t1.smd_after_fixed).abs().max()
    claim("denominators differ by less than 0.001", "differ by less than 0.001 after matching", gap, ok=gap < 0.001)

    # -- Table 8.2 -------------------------------------------------------------
    C = s81.constructed_terms(X)
    record(L, "164 constructed terms", C.shape[1] == 164, f"{C.shape[1]}")
    _, rows, _ = ms_table(s, "8.2")
    summ = {}
    for r in rows:
        if r[0] not in S:
            record(L, f"Table 8.2 row {r[0]} in data", False)
            continue
        g = s81.summary(s81.diagnostics(X, D, *S[r[0]], C=C))
        summ[r[0]] = g
        for j, k in ((1, "smd_max"), (2, "vr_out"), (3, "vr_extreme"), (4, "ks_max"),
                     (5, "con_max"), (6, "con_over_01")):
            cell_(f"Table 8.2 {r[0]} · {k}", g[k], r[j])
    u = s81.diagnostics(X, D, *S["Unadjusted"])
    lv = np.abs(np.log(u["vr"]))
    claim("unadjusted: 1.70 for remoteness", "1.70, for remoteness", u["vr"].iloc[int(lv.values.argmax())],
          ok=lv.idxmax() == "remote" and _agrees(u["vr"]["remote"], "1.70"))
    d = s81.diagnostics(X, D, *S["Propensity score matching"])
    claim("PS matching variance ratios 0.97 to 1.03", "the variance ratios run from 0.97 to 1.03",
          d["vr"].min(), ok=_agrees(d["vr"].min(), "0.97") and _agrees(d["vr"].max(), "1.03"))
    passing = [k for k, g in summ.items() if k != "Unadjusted" and k != "Subclassification, 5 strata"]
    claim("every other adjustment passes every diagnostic", "After any of the adjustments except five strata, every diagnostic passes",
          len(passing), ok=all(summ[k]["smd_max"] < 0.1 and summ[k]["vr_out"] == 0 and summ[k]["con_over_01"] == 0
                               for k in passing)
          and summ["Subclassification, 5 strata"]["con_over_01"] > 0)

    # -- Table 8.3 -------------------------------------------------------------
    t3 = s81.table_8_3(E, D, wt, wc)
    _, rows, _ = ms_table(s, "8.3")
    record(L, "Table 8.3 lists nine variables", len(rows) == len(t3) == 9, f"{len(rows)}")
    for r in rows:
        if r[0] not in t3.index:
            record(L, f"Table 8.3 row {r[0]} in data", False)
            continue
        cell_(f"Table 8.3 {r[0]} · before", t3.before[r[0]], r[1])
        cell_(f"Table 8.3 {r[0]} · after", t3.after[r[0]], r[2])
        record(L, f"Table 8.3 {r[0]} · least balanced category", t3.worst[r[0]] == r[3],
               f"chapter {r[3]} · data {t3.worst[r[0]]}")
    claim("labour force and volatility: 0.286, 0.164 to 0.024, 0.008",
          "at 0.286 and 0.164, are balanced after it at 0.024 and 0.008",
          t3.after["labour_force_status_2016"],
          ok=all(_agrees(t3.loc[v, c], x) for v, c, x in (
              ("labour_force_status_2016", "before", "0.286"), ("earnings_volatility", "before", "0.164"),
              ("labour_force_status_2016", "after", "0.024"), ("earnings_volatility", "after", "0.008"))))
    claim("mutual obligation 0.690 before and 0.689 after", "is imbalanced at 0.690 before matching and 0.689 after",
          t3.after["mutual_obligation_status"],
          ok=_agrees(t3.before["mutual_obligation_status"], "0.690") and _agrees(t3.after["mutual_obligation_status"], "0.689"))

    # -- Script 8.2's draws ----------------------------------------------------
    f = results / "balance_results.csv"
    record(L, "Script 8.2 results present", f.exists(),
           "" if f.exists() else f"run ch08/08_02_diagnostics_across_draws.py first ({results})")
    t = pd.read_csv(f) if f.exists() else None
    ok6 = t is not None and t.seed.nunique() == 6
    if t is not None:
        record(L, "Script 8.2 results cover six draws", ok6,
               f"{t.seed.nunique()} draw(s); --quick output cannot be audited")
    if not ok6:
        return
    ident = (t.est - t.truth - t.y0_gap).abs().max()
    claim("identity holds to a trillionth of a dollar", "differ by less than a trillionth of a dollar", ident,
          ok=ident < 1e-9 * 100 and len(t) == 96)
    claim("96 samples", "across the 96 samples of this chapter", len(t), ok=len(t) == 96)

    ml, mg = s82.means(t, "logit"), s82.means(t, "gbm")
    sdl = t[t.score == "logit"].groupby("sample").bias.std()
    _, rows, _ = ms_table(s, "8.4")
    for r in rows:
        if r[0] not in ml.index:
            record(L, f"Table 8.4 row {r[0]} in data", False)
            continue
        g = ml.loc[r[0]]
        b, sd_ = pair(r[1])
        cell_(f"Table 8.4 {r[0]} · bias", g.bias, b)
        cell_(f"Table 8.4 {r[0]} · bias sd", sdl[r[0]], sd_)
        for j, k in ((2, "smd_max"), (3, "smd_over_005"), (4, "vr_out"), (5, "ks_max"), (6, "con_max")):
            cell_(f"Table 8.4 {r[0]} · {k}", g[k], r[j])
    adj = t[(t.score == "logit") & (t["sample"] != "Unadjusted")]
    okp = adj[(adj.smd_over_01 == 0) & (adj.con_over_01 == 0) & (adj.vr_out == 0)]
    claim("30 of 42 pass every test", f"Of the {len(adj)} adjusted samples on the logistic score, {len(okp)} pass every test",
          len(okp), ok=True)
    claim("their biases run from −23.6 to +12.3", "the biases of those 30 run from −23.6 to +12.3 per cent",
          okp.bias.min(), ok=_agrees(okp.bias.min(), "−23.6") and _agrees(okp.bias.max(), "12.3") and len(okp) == 30)

    Lg = t[t.score == "logit"].set_index(["seed", "sample"])
    diffs = []
    for sd in sorted(t.seed.unique()):
        p, q = Lg.loc[(sd, "Propensity score matching")], Lg.loc[(sd, "Mahalanobis matching")]
        diffs.append(dict(seed=sd, bias=p.bias - q.bias, smd=p.smd_max - q.smd_max, ks=p.ks_max - q.ks_max,
                          con=p.con_max - q.con_max,
                          vr=abs(np.log(p.vr_extreme)) - abs(np.log(q.vr_extreme)),
                          predicted=p.predicted - q.predicted))
    dd = pd.DataFrame(diffs).set_index("seed")
    _, rows, _ = ms_table(s, "8.5")
    record(L, "Table 8.5 has one row per draw", len(rows) == len(dd))
    for r in rows:
        sd = int(r[0])
        for j, k in ((1, "bias"), (2, "smd"), (3, "ks"), (4, "con"), (5, "vr")):
            cell_(f"Table 8.5 {r[0]} · {k}", dd.loc[sd, k], r[j])
    claim("PS more biased in every draw, by 7.6 to 26.8", "by between 7.6 and 26.8 points",
          dd.bias.max(), ok=(dd.bias < 0).all() and _agrees(-dd.bias.max(), "7.6") and _agrees(-dd.bias.min(), "26.8"))
    claim("largest SMD says the opposite in every draw, by 0.026 to 0.058", "by between 0.026 and 0.058",
          dd.smd.max(), ok=(dd.smd < 0).all() and _agrees(-dd.smd.max(), "0.026") and _agrees(-dd.smd.min(), "0.058"))

    # Table 8.6
    g = t[t.score == "gbm"]
    _, rows, _ = ms_table(s, "8.6")
    for r in rows:
        q = g[g["sample"] == r[0]]
        if not len(q):
            record(L, f"Table 8.6 row {r[0]} in data", False)
            continue
        cell_(f"Table 8.6 {r[0]} · bias", q.bias.mean(), r[1].replace("%", ""))
        cell_(f"Table 8.6 {r[0]} · largest SMD", q.smd_max.mean(), r[2])
        f1, f5 = int((q.smd_over_01 > 0).sum()), int((q.smd_over_005 > 0).sum())
        record(L, f"Table 8.6 {r[0]} · failing 0.1", r[3] == f"{f1} of {len(q)}", f"chapter {r[3]} · data {f1}")
        record(L, f"Table 8.6 {r[0]} · failing 0.05", r[4] == f"{f5} of {len(q)}", f"chapter {r[4]} · data {f5}")
    pm = g[g["sample"] == "Propensity score matching"]
    claim("remoteness least balanced most often", "with remoteness the least balanced covariate most often",
          0, ok=pm.smd_worst.mode()[0] == "remote")
    k20 = g[g["sample"] == "Subclassification, 20 strata"]
    claim("boosted 20 strata: largest SMD 0.083 to 0.104", "of between 0.083 and 0.104 across the six draws",
          k20.smd_max.min(), ok=_agrees(k20.smd_max.min(), "0.083") and _agrees(k20.smd_max.max(), "0.104"))
    claim("... pass 0.1 in five draws of six", "pass the 0.1 threshold in five draws of six",
          int((k20.smd_over_01 == 0).sum()), ok=int((k20.smd_over_01 == 0).sum()) == 5)
    claim("... bias +9.4 to +23.1", "biased by between +9.4 and +23.1 per cent",
          k20.bias.min(), ok=_agrees(k20.bias.min(), "9.4") and _agrees(k20.bias.max(), "23.1"))
    others = [k for k in s82.ORDER[1:] if k != "Odds weighting"]
    claim("at 0.05 every sample but odds weighting fails in five draws or more",
          "every sample in Table 8.6 except odds weighting fails in at least five draws",
          0, ok=all(int((g[g["sample"] == k].smd_over_005 > 0).sum()) >= 5 for k in others)
          and int((g[g["sample"] == "Odds weighting"].smd_over_005 > 0).sum()) == 0)
    sm = [mg.smd_max[f"Subclassification, {k} strata"] for k in (5, 20, 100)]
    sb = [mg.bias[f"Subclassification, {k} strata"] for k in (5, 20, 100)]
    claim("balance 0.061, 0.093, 0.125 as strata are added", "rising from 0.061 at five strata to 0.093 at twenty and 0.125 at a hundred",
          sm[0], ok=all(_agrees(a, b) for a, b in zip(sm, ("0.061", "0.093", "0.125"))))
    claim("bias +2.0, +16.4, +20.0", "while the bias rises from +2.0 to +16.4 and +20.0 per cent",
          sb[0], ok=all(_agrees(a, b) for a, b in zip(sb, ("2.0", "16.4", "20.0"))))
    claim("logistic: adding strata improved balance", "On the logistic score of Table 8.4, adding strata improved balance",
          0, ok=ml.smd_max["Subclassification, 5 strata"] > ml.smd_max["Subclassification, 20 strata"]
          > ml.smd_max["Subclassification, 100 strata"])

    # Table 8.7
    _, rows, _ = ms_table(s, "8.7")
    for r in rows:
        cell_(f"Table 8.7 {r[0]} · logistic actual", ml.bias[r[0]], r[1].replace("%", ""))
        cell_(f"Table 8.7 {r[0]} · logistic predicted", ml.predicted[r[0]], r[2].replace("%", ""))
        cell_(f"Table 8.7 {r[0]} · boosted actual", mg.bias[r[0]], r[3].replace("%", ""))
        cell_(f"Table 8.7 {r[0]} · boosted predicted", mg.predicted[r[0]], r[4].replace("%", ""))
    claim("predicted above actual in every row", "in every row of Table 8.7 the predicted bias lies above the actual bias",
          0, ok=bool(((ml.predicted - ml.bias) > 0).all() and ((mg.predicted - mg.bias) > 0).all()))
    a_ = t[t["sample"] != "Unadjusted"]
    p_ = a_[a_.smd_over_01 == 0]
    cor = lambda d_, c: float(np.corrcoef(d_.bias, d_[c])[0, 1])       # noqa: E731
    claim("84 samples: 0.97 against −0.27 and −0.19",
          f"Across the {len(a_)} adjusted samples of the two scores, the predicted bias correlates at 0.97",
          cor(a_, "predicted"), ok=_agrees(cor(a_, "predicted"), "0.97") and _agrees(cor(a_, "smd_max"), "−0.27")
          and _agrees(cor(a_, "ks_max"), "−0.19"))
    claim("51 passing: 0.88 against 0.45 and 0.63", f"Among the {len(p_)} samples that pass the 0.1 threshold",
          cor(p_, "predicted"), ok=_agrees(cor(p_, "predicted"), "0.88") and _agrees(cor(p_, "smd_max"), "0.45")
          and _agrees(cor(p_, "ks_max"), "0.63"))
    claim("check sees PS worse in every draw, by 4.4 to 16.0, 10.3 on average, against 15.1",
          "by between 4.4 and 16.0 points and by 10.3 on average, against an actual difference of 15.1",
          dd.predicted.mean(), ok=(dd.predicted < 0).all() and _agrees(-dd.predicted.max(), "4.4")
          and _agrees(-dd.predicted.min(), "16.0") and _agrees(-dd.predicted.mean(), "10.3")
          and _agrees(-dd.bias.mean(), "15.1"))
    record(L, "no table or claim quotes the unobserved confounders (Chapter 10)",
           "u_employability" not in prose and "earnings_shock" not in prose)


CH9_RECOMMENDED = {"odds": "se_sandwich", "ipw_ate": "se_sandwich", "dr_att": "se_boot",
                   "dr_ate": "se_boot", "sub20": "se_boot", "sub20_reg": "se_boot",
                   "match": "se_paired", "match_repl": "se_ai", "maha": "se_paired",
                   "maha13": "se_paired"}
CH9_ROWS = {"ATT: odds weighting": "odds", "ATT: doubly robust": "dr_att",
            "ATT: subclassification, 20 strata": "sub20",
            "ATT: 20 strata, regression within strata": "sub20_reg",
            "ATT: PS matching, 1:1": "match", "ATT: PS matching, with replacement": "match_repl",
            "ATT: Mahalanobis matching, 1:1": "maha", "ATT: Mahalanobis matching, 1:3": "maha13",
            "ATE: normalised IPW": "ipw_ate", "ATE: doubly robust": "dr_ate",
            "Odds weighting": "odds", "Doubly robust": "dr_att",
            "Subclassification, 20 strata": "sub20",
            "20 strata, regression within strata": "sub20_reg", "PS matching, 1:1": "match",
            "Mahalanobis matching, 1:1": "maha", "Mahalanobis matching, 1:3": "maha13",
            "Normalised IPW (ATE)": "ipw_ate"}


def ch9_committed(repo: Path):
    f = repo / "results" / "ch09_standard_errors_200.csv"
    if not f.exists():
        return None
    t = pd.read_csv(f)
    return t.assign(err=t.est - t.truth, bias=100 * (t.est - t.truth) / t.truth)


def layer_e9(s: str, repo: Path, data: Path, results: Path) -> None:
    L = "E chapter 9"
    prose = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)

    def cell_(check, got, shown):
        record(L, check, _agrees(got, shown), f"chapter {shown} · data {got:,.4f}")

    def claim(label, snippet, got, shown=None, ok=None):
        if snippet.lower() not in prose.lower():
            record(L, f"claim: {label}", False, f"text not found: '{snippet}'")
            return
        ok = _agrees(got, shown) if ok is None else ok
        det = (f"chapter {shown} · data {got:,.4f}" if shown is not None
               else f"data {got:,.4f}" if isinstance(got, (int, float, np.floating, np.integer)) else str(got))
        record(L, f"claim: {label}", bool(ok), det)

    money = lambda x: x.replace("$", "")                                    # noqa: E731

    # -- Table 9.1 and Sections 9.3, 9.7, 9.8: Script 9.1's output ----------
    f = results / "primary_estimates.csv"
    record(L, "Script 9.1 results present", f.exists(),
           "" if f.exists() else f"run ch09/09_01_estimate_primary.py first ({results})")
    if f.exists():
        p = pd.read_csv(f).set_index("estimator")
        quoted = {"odds": "se_naive", "ipw_ate": "se_naive", "dr_att": "se_naive", "dr_ate": "se_naive",
                  "sub20": "se_naive", "sub20_reg": None, "match": "se_paired",
                  "match_repl": "se_paired", "maha": "se_paired", "maha13": "se_paired"}
        names = {"se_sandwich": "sandwich", "se_boot": "bootstrap", "se_paired": "paired",
                 "se_ai": "Abadie–Imbens"}
        _, rows, cap = ms_table(s, "9.1")
        for r in rows:
            k = CH9_ROWS[r[0]]
            g = p.loc[k]
            m = CH9_RECOMMENDED[k]
            cell_(f"Table 9.1 {r[0]} · estimate", g.est, money(r[1]))
            if quoted[k]:
                cell_(f"Table 9.1 {r[0]} · SE as quoted", g[quoted[k]], money(r[2]))
            cell_(f"Table 9.1 {r[0]} · SE", g[m], money(r[3]))
            record(L, f"Table 9.1 {r[0]} · method", r[4] == names[m], f"chapter {r[4]} · {m}")
            lo, hi = [money(x) for x in r[5].split(" to ")]
            cell_(f"Table 9.1 {r[0]} · lower", g.est - 1.96 * g[m], lo)
            cell_(f"Table 9.1 {r[0]} · upper", g.est + 1.96 * g[m], hi)
        att = [p.loc[CH9_ROWS[r[0]], "est"] for r in rows if r[0].startswith("ATT")]
        claim("ATT estimates range $4,921 to $6,640", "range from $4,921 to $6,640",
              min(att), ok=_agrees(min(att), "4,921") and _agrees(max(att), "6,640"))
        claim("PS interval ends at $5,790, Mahalanobis begins at $5,979",
              "the propensity score matched interval ends at $5,790 and the Mahalanobis matched interval begins at $5,979",
              0, ok=_agrees(p.loc["match", "est"] + 1.96 * p.loc["match", "se_paired"], "5,790")
              and _agrees(p.loc["maha", "est"] - 1.96 * p.loc["maha", "se_paired"], "5,979"))
        o, ia, mm, mr = p.loc["odds"], p.loc["ipw_ate"], p.loc["match"], p.loc["match_repl"]
        claim("odds: naive $366, sandwich $241", "The naive standard error of odds weighting is $366, and the sandwich standard error is $241",
              o.se_sandwich, ok=_agrees(o.se_naive, "366") and _agrees(o.se_sandwich, "241"))
        claim("ATE: $606 and $494", "for the normalised ATE the figures are $606 and $494",
              ia.se_sandwich, ok=_agrees(ia.se_naive, "606") and _agrees(ia.se_sandwich, "494"))
        claim("bootstrap $240 and $475", "the full bootstrap gives $240 for odds weighting",
              o.se_boot, ok=_agrees(o.se_boot, "240") and _agrees(ia.se_boot, "475"))
        claim("paired $443 against unpaired $507", "is $443, against $507",
              mm.se_paired, ok=_agrees(mm.se_paired, "443") and _agrees(mm.se_unpaired, "507"))
        claim("Abadie-Imbens $463 against paired $443", "it is $463, against a paired standard error of $443",
              mr.se_ai, ok=_agrees(mr.se_ai, "463") and _agrees(mr.se_paired, "443"))
        claim("4,864 pairs, 4,290 distinct, reuse at most four", "of 4,864 pairs formed with replacement on the primary dataset, 4,290 distinct controls appear",
              mr.pairs, ok=int(mr.pairs) == 4864 and int(mr.distinct) == 4290 and int(mr.max_reuse) == 4)
        claim("difference $50, SE $59 against $350, correlation 0.97",
              "differ by $50, and the bootstrap standard error of that difference is $59, against $350",
              o.se_diff_dr_odds, ok=_agrees(abs(p.loc["dr_att", "est"] - o.est), "50")
              and _agrees(o.se_diff_dr_odds, "59")
              and _agrees(np.sqrt(p.loc["dr_att", "se_boot"] ** 2 + o.se_boot ** 2), "350")
              and _agrees(o.corr_dr_odds, "0.97"))
        claim("true ATT $6,408 and ATE $5,412", "The true ATT on the primary dataset is $6,408",
              o.truth_att, ok=_agrees(o.truth_att, "6,408") and _agrees(o.truth_ate, "5,412")
              and "The true ATE is $5,412" in prose)
        gap = max(abs(p.loc[k, "truth"] - o.truth_att) for k in ("match", "match_repl", "maha", "maha13"))
        claim("matched truths within $33", "differs from it by no more than $33", gap, ok=round(gap) <= 33)
        inside = {k: abs(p.loc[k, "est"] - p.loc[k, "truth"]) <= 1.96 * p.loc[k, CH9_RECOMMENDED[k]]
                  for k in ("odds", "dr_att", "sub20", "sub20_reg", "match", "match_repl", "maha", "maha13")}
        claim("only the two Mahalanobis intervals contain the truth", "Of the eight intervals for the ATT in Table 9.1, two contain it",
              sum(inside.values()), ok=sum(inside.values()) == 2 and inside["maha"] and inside["maha13"])
        ate_in = [abs(p.loc[k, "est"] - p.loc[k, "truth"]) <= 1.96 * p.loc[k, CH9_RECOMMENDED[k]]
                  for k in ("ipw_ate", "dr_ate")]
        claim("neither ATE interval contains the truth", "neither interval for the ATE contains it",
              0, ok=not any(ate_in))

    # -- The committed 200-draw run -----------------------------------------
    t = ch9_committed(repo)
    record(L, "committed 200-draw results present", t is not None,
           "results/ch09_standard_errors_200.csv")
    if t is None:
        return
    nd, nb = t.seed.nunique(), t.dropna(subset=["se_boot"]).seed.nunique()
    record(L, "committed run: 200 draws, bootstrap on 40", (nd, nb) == (200, 40), f"{nd}, {nb}")
    run = results / "se_results.csv"
    if run.exists():
        r = pd.read_csv(run)
        m = r.merge(t, on=["seed", "estimator"], suffixes=("", "_c"))
        cols = [c for c in ("est", "truth", "se_naive", "se_sandwich", "se_paired", "se_ai", "se_boot")
                if c in r and c + "_c" in m]
        gap = max(float(np.nanmax(np.abs(m[c] - m[c + "_c"]))) if m[c].notna().any() else 0.0 for c in cols)
        record(L, "this run reproduces the committed rows", len(m) == len(r) and gap < 1e-6,
               f"{len(m)} rows, largest difference {gap:.1e}")
    else:
        record(L, "Script 9.2 results present", False,
               f"run ch09/09_02_standard_errors_across_draws.py first ({results})")
    sp = t.groupby("estimator").err.std()
    sp_b = t.dropna(subset=["se_boot"]).groupby("estimator").err.std()
    ratio = lambda k, m: (t[t.estimator == k][m].mean()                    # noqa: E731
                          / (sp_b[k] if m == "se_boot" else sp[k]))
    cols = {1: None, 2: "se_naive", 3: "se_sandwich", 4: "se_boot", 5: "se_paired",
            6: "se_unpaired", 7: "se_ai", 8: "se_wls_robust"}
    _, rows, _ = ms_table(s, "9.2")
    for r in rows:
        k = CH9_ROWS[r[0]]
        cell_(f"Table 9.2 {r[0]} · spread", sp[k], money(r[1]))
        for j in range(2, 9):
            has = cols[j] in t and t[t.estimator == k][cols[j]].notna().any()
            if r[j]:
                cell_(f"Table 9.2 {r[0]} · {cols[j]}", ratio(k, cols[j]) if has else np.nan, r[j])
            else:
                record(L, f"Table 9.2 {r[0]} · {cols[j]} blank", not has)
    q = t[t.estimator == "ipw_ate"]
    o = t[t.estimator == "odds"]
    claim("default WLS 0.58 for the ATE", "it is 0.58 of the actual spread", q.se_wls_default.mean() / sp["ipw_ate"], "0.58")
    claim("default WLS 1.01 for odds", "almost right, at 1.01", o.se_wls_default.mean() / sp["odds"], "1.01")
    claim("frequency convention 0.41 and 2.12", "at 0.41 for the ATE and 2.12 for the ATT",
          q.se_wls_freq.mean() / sp["ipw_ate"], ok=_agrees(q.se_wls_freq.mean() / sp["ipw_ate"], "0.41")
          and _agrees(o.se_wls_freq.mean() / sp["odds"], "2.12"))
    claim("matched-set bootstrap 1.23 and 1.14", "(1.23 for one-to-one matching and 1.14 under replacement)",
          ratio("match", "se_boot_sets"), ok=_agrees(ratio("match", "se_boot_sets"), "1.23")
          and _agrees(ratio("match_repl", "se_boot_sets"), "1.14"))
    claim("reuse adds four per cent", "adds only four per cent to the paired standard error",
          ratio("match_repl", "se_ai") / ratio("match_repl", "se_paired"),
          ok=_agrees(100 * (ratio("match_repl", "se_ai") / ratio("match_repl", "se_paired") - 1), "4"))

    # Table 9.3
    _, rows, _ = ms_table(s, "9.3")
    for r in rows:
        k = CH9_ROWS[r[0].replace(", score known", "")]
        m = "se_naive" if "score known" in r[0] else CH9_RECOMMENDED[k]
        q = t[t.estimator == k].dropna(subset=[m])
        mu = q.err.mean()
        cell_(f"Table 9.3 {r[0]} · bias", q.bias.mean(), r[2].replace("%", ""))
        cell_(f"Table 9.3 {r[0]} · bias in SEs", mu / q[m].mean(), r[3])
        cell_(f"Table 9.3 {r[0]} · covers truth", 100 * (np.abs(q.err) <= 1.96 * q[m]).mean(), r[4].replace("%", ""))
        cell_(f"Table 9.3 {r[0]} · covers own mean", 100 * (np.abs(q.err - mu) <= 1.96 * q[m]).mean(),
              r[5].replace("%", ""))

    def cover(k, m, centred=False):
        q = t[t.estimator == k].dropna(subset=[m])
        mu = q.err.mean() if centred else 0.0
        return 100 * (np.abs(q.err - mu) <= 1.96 * q[m]).mean()
    claim("odds covers the truth 18 per cent", "contains the true ATT in only 18 per cent of draws",
          cover("odds", "se_sandwich"), "18")
    claim("DR and 20 strata: 8 and 12 per cent", "in 8 and 12 per cent",
          cover("dr_att", "se_boot"), ok=_agrees(cover("dr_att", "se_boot"), "8")
          and _agrees(cover("sub20", "se_boot"), "12"))
    claim("naive covers 54 per cent against 18", "covers the truth 54 per cent of the time, against 18 per cent",
          cover("odds", "se_naive"), ok=_agrees(cover("odds", "se_naive"), "54"))
    cen = [cover(k, CH9_RECOMMENDED[k], True) for k in CH9_RECOMMENDED]
    claim("centred coverage 92 to 98", "cover 92 to 98 per cent of the time", min(cen),
          ok=_agrees(min(cen), "92") and _agrees(max(cen), "98"))
    claim("naive overstates by 54 and 20 per cent", "overstates the spread by 54 per cent for odds weighting and by 20 per cent",
          ratio("odds", "se_naive"), ok=_agrees(100 * (ratio("odds", "se_naive") - 1), "54")
          and _agrees(100 * (ratio("ipw_ate", "se_naive") - 1), "20"))
    claim("PS matching conservative: 24, 42 and 18 per cent", "the paired standard error by 24 per cent, the unpaired by 42 per cent",
          ratio("match", "se_paired"), ok=_agrees(100 * (ratio("match", "se_paired") - 1), "24")
          and _agrees(100 * (ratio("match", "se_unpaired") - 1), "42")
          and _agrees(100 * (ratio("match_repl", "se_ai") - 1), "18"))

    # Table 9.4
    w = t.pivot(index="seed", columns="estimator", values="bias")
    blocks = w.iloc[:198].groupby(np.arange(198) // 6).mean()
    _, rows, _ = ms_table(s, "9.4")
    for r in rows:
        k = CH9_ROWS[r[0]]
        cell_(f"Table 9.4 {r[0]} · six mean", w[k].iloc[:6].mean(), r[1].replace("%", ""))
        cell_(f"Table 9.4 {r[0]} · six sd", w[k].iloc[:6].std(), r[2])
        cell_(f"Table 9.4 {r[0]} · 200 mean", w[k].mean(), r[3].replace("%", ""))
        cell_(f"Table 9.4 {r[0]} · 200 sd", w[k].std(), r[4])
        rank = int((blocks[k] < blocks[k].iloc[0]).sum()) + 1
        record(L, f"Table 9.4 {r[0]} · rank", str(rank) == r[5], f"chapter {r[5]} · data {rank}")
    claim("six-draw means reproduce Chapter 5's", "fifteen points across the six draws, is 8.6 points across 200",
          (w["match"] - w["maha"]).mean(), ok=_agrees(-(w["match"] - w["maha"]).iloc[:6].mean(), "15")
          and _agrees(-(w["match"] - w["maha"]).mean(), "8.6"))
    claim("PS more biased in 91 per cent", "in 91 per cent of the 200 draws",
          100 * ((w["match"] - w["maha"]) < 0).mean(), "91")
    claim("200-draw SE 0.3 and 0.4", "of about 0.3 points for the weighting estimators and 0.4 for matching",
          w["odds"].std() / np.sqrt(200), ok=_agrees(w["odds"].std() / np.sqrt(200), "0.3")
          and _agrees(w["match"].std() / np.sqrt(200), "0.4"))

    # Table 9.5
    _, rows, _ = ms_table(s, "9.5")
    pairs = {"PS matching less Mahalanobis matching, 1:1": ("match", "maha"),
             "Mahalanobis 1:3 less Mahalanobis 1:1": ("maha13", "maha"),
             "20 strata with regression less without": ("sub20_reg", "sub20"),
             "Doubly robust less odds weighting": ("dr_att", "odds"),
             "PS matching with replacement less without": ("match_repl", "match")}
    for r in rows:
        a_, b_ = pairs[r[0]]
        d = w[a_] - w[b_]
        cell_(f"Table 9.5 {r[0]} · mean", d.mean(), r[1])
        cell_(f"Table 9.5 {r[0]} · sd", d.std(), r[2])
        cell_(f"Table 9.5 {r[0]} · sd each", (w[a_].std() + w[b_].std()) / 2, r[3])
        cell_(f"Table 9.5 {r[0]} · same sign", 100 * (np.sign(d) == np.sign(d.mean())).mean(), r[4].replace("%", ""))
        cell_(f"Table 9.5 {r[0]} · independent", np.sqrt(w[a_].std() ** 2 + w[b_].std() ** 2), r[5])
    rm = {k: np.sqrt((w[k] ** 2).mean()) for k in ("maha", "maha13")}
    claim("Mahalanobis 1:3: sd 5.4 to 4.1, bias -3.3 against -1.3, RMSE 5.2 against 5.5",
          "from 5.4 to 4.1 points and costs about two points of bias (−3.3 against −1.3 per cent)",
          w["maha13"].std(), ok=_agrees(w["maha"].std(), "5.4") and _agrees(w["maha13"].std(), "4.1")
          and _agrees(w["maha13"].mean(), "-3.3") and _agrees(w["maha"].mean(), "-1.3")
          and _agrees(rm["maha13"], "5.2") and _agrees(rm["maha"], "5.5"))
    record(L, "no claim names the unobserved confounders (Chapter 10)",
           "u_employability" not in prose and "earnings_shock" not in prose)


CH10_PREV = {"+ 2016 earnings in dollars and age squared": "Chapter 3's score",
             "+ education as categories and English proficiency": "+ 2016 earnings in dollars and age squared",
             "+ the pre-programme earnings shock (truth file)": "+ education as categories and English proficiency",
             "+ employability (truth file)": "+ education as categories and English proficiency",
             "Employability alone (truth file)": "Chapter 3's score",
             "+ mutual obligation status": "+ education as categories and English proficiency",
             "The true propensity score": "Chapter 3's score"}


def layer_e10(s: str, repo: Path, data: Path, results: Path) -> None:
    L = "E chapter 10"
    prose = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)

    def cell_(check, got, shown):
        record(L, check, _agrees(got, shown), f"chapter {shown} · data {got:,.4f}")

    def claim(label, snippet, got, shown=None, ok=None):
        if snippet.lower() not in prose.lower():
            record(L, f"claim: {label}", False, f"text not found: '{snippet}'")
            return
        ok = _agrees(got, shown) if ok is None else ok
        det = (f"chapter {shown} · data {got:,.4f}" if shown is not None
               else f"data {got:,.4f}" if isinstance(got, (int, float, np.floating, np.integer)) else str(got))
        record(L, f"claim: {label}", bool(ok), det)

    money = lambda x: x.replace("$", "")                                    # noqa: E731
    pc = lambda x: x.replace("%", "")                                       # noqa: E731

    # -- Script 10.1: Tables 10.1 and 10.5, Sections 10.2 and 10.4.3 --------
    f = results / "sources_of_bias.csv"
    record(L, "Script 10.1 results present", f.exists(),
           "" if f.exists() else f"run ch10/10_01_sources_of_bias.py first ({results})")
    if f.exists():
        t = pd.read_csv(f)
        nd = t.seed.nunique()
        record(L, "Script 10.1 ran 40 draws", nd == 40, f"{nd} draws")
        sp = t[t.kind == "spec"]
        w = {c: sp.pivot(index="seed", columns="name", values=c) for c in ("odds", "dr", "maha")}
        _, rows, cap = ms_table(s, "10.1")
        for r in rows:
            k = r[0]
            cell_(f"Table 10.1 {k} · odds", w["odds"][k].mean(), pc(r[1]))
            cell_(f"Table 10.1 {k} · DR", w["dr"][k].mean(), pc(r[2]))
            cell_(f"Table 10.1 {k} · Mahalanobis", w["maha"][k].mean(), pc(r[3]))
            if k in CH10_PREV:
                d = w["odds"][k] - w["odds"][CH10_PREV[k]]
                cell_(f"Table 10.1 {k} · change", d.mean(), r[4])
                cell_(f"Table 10.1 {k} · SE of change", d.std() / np.sqrt(nd), r[5])
            else:
                record(L, f"Table 10.1 {k} · change blank", r[4] == "" and r[5] == "")
        o = w["odds"]
        base, obs = "Chapter 3's score", "+ education as categories and English proficiency"
        claim("form removes 3.2 points, SE 0.18", "removes 3.2 points of bias, and the standard error of that improvement, 0.18",
              (o["+ 2016 earnings in dollars and age squared"] - o[base]).mean(), "3.2")
        claim("employability removes 4.0, alone 4.1", "Adding it to the model removes 4.0 points of bias, and adding it alone to Chapter 3's model removes 4.1",
              (o["+ employability (truth file)"] - o[obs]).mean(), "4.0")
        claim("shock moves the bias by half a point", "Adding the shock to the model moves the bias by half a point",
              (o["+ the pre-programme earnings shock (truth file)"] - o[obs]).mean(),
              ok=0.3 <= (o["+ the pre-programme earnings shock (truth file)"] - o[obs]).mean() <= 0.7)
        mo = "+ mutual obligation status"
        claim("near-instrument: sd rises, Mahalanobis -2.0 to -4.6",
              f"raises its standard deviation across draws from {o[obs].std():.1f} points to {o[mo].std():.1f}",
              o[mo].std(), ok=abs(o[mo].mean() - o[obs].mean()) < 0.1
              and _agrees(w["maha"][obs].mean(), "-2.0") and _agrees(w["maha"][mo].mean(), "-4.6")
              and "from −2.0 to −4.6 per cent" in prose)
        claim("after both corrections 3.3 low; true score 1.5 low, sd 10.9",
              "odds weighting is 3.3 per cent low. Weighting by the true propensity score is 1.5 per cent low, but with a standard deviation of 10.9 points",
              o["+ employability (truth file)"].mean(),
              ok=_agrees(o["+ employability (truth file)"].mean(), "-3.3")
              and _agrees(o["The true propensity score"].mean(), "-1.5")
              and _agrees(o["The true propensity score"].std(), "10.9"))
        claim("eleven points of bias", "decomposes the eleven points of bias", o[base].mean(),
              ok=round(-o[base].mean()) == 11)
        lr = t[t.kind == "lr"].set_index("seed")
        claim("LR test on the primary dataset: 10.4, p = 0.001",
              "the statistic is 10.4 on one degree of freedom, with a p-value of 0.001",
              lr.loc[20260808, "odds"], ok=_agrees(lr.loc[20260808, "odds"], "10.4")
              and _agrees(lr.loc[20260808, "dr"], "0.001"))
        claim("LR test rejects in 28 of 40", "the test rejects at the five per cent level in 28",
              int((lr.dr < 0.05).sum()), ok=int((lr.dr < 0.05).sum()) == 28
              and "missed the term about three times in ten" in prose)

        g = t[t.kind == "group"]
        _, rows, _ = ms_table(s, "10.5")
        for r in rows:
            q = g[g.name == r[0]]
            cell_(f"Table 10.5 {r[0]} · treated", q.maha.mean(), r[1])
            cell_(f"Table 10.5 {r[0]} · estimate", q.odds.mean(), money(r[2]))
            cell_(f"Table 10.5 {r[0]} · truth", q.dr.mean(), money(r[3]))
            for j, c in ((4, "odds"), (5, "obs"), (6, "emp")):
                cell_(f"Table 10.5 {r[0]} · bias, {c}", (100 * (q[c] - q.dr) / q.dr).mean(), pc(r[j]))
        gm = g.groupby("name")[["odds", "dr"]].mean()
        est_gap = gm.loc["Low education (Year 12 or less)", "odds"] - gm.loc["Higher education", "odds"]
        true_gap = gm.loc["Low education (Year 12 or less)", "dr"] - gm.loc["Higher education", "dr"]
        claim("education gap almost $3,900 against about $2,600",
              "the estimated gap is almost $3,900 and the true gap about $2,600", est_gap,
              ok=3800 <= est_gap < 3900 and 2550 <= true_gap < 2650)

        adv = ["Higher education", "Not a long-term recipient", "No earnings dip"]
        bb = {c: (100 * (g[c] - g.dr) / g.dr).groupby(g.name).mean() for c in ("odds", "obs", "emp")}
        half1 = [bb["obs"][k] / bb["odds"][k] for k in adv]
        half2 = [bb["emp"][k] / bb["obs"][k] for k in adv]
        claim("observed terms halve the bias; employability about half the rest",
              "Correcting how the covariates entered halves the bias in the less disadvantaged groups", min(half1),
              ok=all(0.4 <= h <= 0.6 for h in half1) and all(0.35 <= h <= 0.65 for h in half2)
              and "adding employability removes about half of what remains" in prose)
        claim("advantaged groups 19 to 26 per cent low", "they are between 19 and 26 per cent low",
              min(-bb["odds"][k] for k in adv), ok=round(min(-bb["odds"][k] for k in adv)) == 19
              and round(max(-bb["odds"][k] for k in adv)) == 26)
        y_ = t[t.kind == "year"]
        ym = y_.groupby("name")[["odds", "dr", "maha"]].mean()
        ym.index = ym.index.astype(str)
        claim("time path -$6,034, +$1,802, +$5,724",
              "is −$6,034 in 2017, +$1,802 in 2018 and +$5,724 in 2019", ym.loc["2017", "odds"],
              ok=_agrees(ym.loc["2017", "odds"], "-6,034") and _agrees(ym.loc["2018", "odds"], "1,802")
              and _agrees(ym.loc["2019", "odds"], "5,724"))
        claim("observed for 86 and 82 per cent",
              "2017 earnings are observed for 86 per cent of the analysis file and 2018 earnings for 82 per cent",
              100 * ym.loc["2017", "maha"], ok=_agrees(100 * ym.loc["2017", "maha"], "86")
              and _agrees(100 * ym.loc["2018", "maha"], "82"))
        claim("implied 2018 truth +$3,541, estimate about half",
              "implies a true effect of +$3,541 in 2018", ym.loc["2018", "dr"],
              ok=_agrees(ym.loc["2018", "dr"], "3,541")
              and 0.45 <= ym.loc["2018", "odds"] / ym.loc["2018", "dr"] <= 0.55)

    # -- Script 10.2: Tables 10.2, 10.3 and 10.4, the primary dataset -------
    f = results / "sensitivity_primary.csv"
    record(L, "Script 10.2 results present", f.exists(),
           "" if f.exists() else f"run ch10/10_02_sensitivity.py first ({results})")
    if not f.exists():
        return
    v = pd.read_csv(f).set_index("quantity")["value"].to_dict()
    keys = {"highest education": "edu", "log earnings 2016": "log_inc_2016",
            "fortnights on payment 2016": "fn_2016"}
    _, rows, cap = ms_table(s, "10.2")
    for r in rows:
        if r[0].startswith("Employability"):
            dz, yz, b = v["u_dz"], v["u_yz"], v["u_bias"]
        else:
            mult = 3 if r[0].startswith("Three") else 1
            k = keys[r[0].lower().split("as strong as ")[1]]
            dz, yz, b = (v[f"bench_{k}_{mult}_{x}"] for x in ("dz", "yz", "bias"))
        cell_(f"Table 10.2 {r[0]} · R2 treatment", dz, r[1])
        cell_(f"Table 10.2 {r[0]} · R2 earnings", yz, r[2])
        cell_(f"Table 10.2 {r[0]} · bias", b, money(r[3]))
    claim("regression $6,027 (se $320)", "gives an estimate of $6,027 with a standard error of $320", v["est"],
          ok=_agrees(v["est"], "6,027") and _agrees(v["se"], "320")
          and "estimate $6,027, standard error $320" in cap)
    claim("partial R2 0.0083", "here 0.0083, meaning", v["r2_yd"], "0.0083")
    claim("robustness value 0.087", "here 0.087, or 8.7 per cent", v["rv"], "0.087")
    claim("RV for $5,000 is 0.015", "To bring the estimate down to $5,000, the robustness value is 0.015", v["rv_5000"], "0.015")
    claim("education benchmarks $255 and $766", "would shift the estimate by at most $255, and one three times as strong by at most $766",
          v["bench_edu_1_bias"], ok=_agrees(v["bench_edu_1_bias"], "255") and _agrees(v["bench_edu_3_bias"], "766"))
    claim("4.0 and 23.3 times education", "would have to be 4.0 times as strong as education; to bring it to zero, 23.3 times as strong",
          v["k_edu_5000"], ok=_agrees(v["k_edu_5000"], "4.0") and _agrees(v["k_edu_0"], "23.3"))
    claim("box: more than twenty, about four times", "more than twenty times as influential as education",
          v["k_edu_0"], ok=20 < v["k_edu_0"] < 25 and 3.5 <= v["k_edu_5000"] < 4.5
          and "it would have to be about four times as influential" in prose)
    claim("employability 0.0018, 0.0148, $342", "Employability's partial R-squareds are 0.0018 with treatment and 0.0148 with earnings",
          v["u_dz"], ok=_agrees(v["u_dz"], "0.0018") and _agrees(v["u_yz"], "0.0148")
          and _agrees(v["u_bias"], "342") and "the bound gives $342" in prose)
    claim("refit $6,368, shift $342", "moves the estimate to $6,368, a shift of exactly $342", v["u_refit"],
          ok=_agrees(v["u_refit"], "6,368") and _agrees(v["u_refit"] - v["est"], "342")
          and abs((v["u_refit"] - v["est"]) - v["u_bias"]) < 1)
    claim("employability a little stronger than education", "a little stronger than education", v["u_dz"],
          ok=v["u_dz"] > v["bench_edu_1_dz"] and v["u_yz"] > v["bench_edu_1_yz"]
          and v["u_bias"] < v["bench_edu_3_bias"])
    claim("benchmarks under a fifth of one per cent", "each benchmark covariate explains less than a fifth of one per cent",
          max(v[f"bench_{k}_1_dz"] for k in keys.values()),
          ok=max(v[f"bench_{k}_1_dz"] for k in keys.values()) < 0.002)

    _, rows, _ = ms_table(s, "10.3")
    for r in rows:
        k = "maha" if r[0].startswith("Mahal") else "ps"
        cell_(f"Table 10.3 {r[0]} · estimate", v[f"est_{k}"], money(r[1]))
        for j, t_ in ((2, 0), (3, 2500), (4, 5000)):
            cell_(f"Table 10.3 {r[0]} · gamma {t_}", v[f"gamma_{k}_{t_}"], r[j])
        cell_(f"Table 10.3 {r[0]} · employability median", v[f"uo_med_{k}"], r[5])
        cell_(f"Table 10.3 {r[0]} · employability p95", v[f"uo_p95_{k}"], r[6])
    claim("Mahalanobis survives to 2.29, $5,000 only to 1.20", "would survive hidden bias up to Γ = 2.29",
          v["gamma_maha_0"], ok=_agrees(v["gamma_maha_0"], "2.29") and _agrees(v["gamma_maha_5000"], "1.20")
          and "surviving only up to Γ = 1.20" in prose)
    claim("PS matching 1.68, 1.32, 1.03", "at 1.68, 1.32 and 1.03", v["gamma_ps_0"],
          ok=all(_agrees(v[f"gamma_ps_{t_}"], x) for t_, x in ((0, "1.68"), (2500, "1.32"), (5000, "1.03"))))
    claim("Hodges-Lehmann $5,762", "the Hodges–Lehmann estimate, is $5,762", v["hl_ps"],
          ok=_agrees(v["hl_ps"], "5,762") and v["est_ps"] < 5000 < v["hl_ps"] and v["gamma_ps_5000"] > 1)
    claim("employability odds 1.17 and 1.56, below Γ for a positive effect",
          "by a median factor of 1.17, and by 1.56 in the 95th percentile", v["uo_med_maha"],
          ok=_agrees(v["uo_med_maha"], "1.17") and _agrees(v["uo_p95_maha"], "1.56")
          and v["uo_p95_maha"] < v["gamma_maha_0"] and v["uo_p95_ps"] < v["gamma_ps_0"]
          and v["uo_med_maha"] >= v["gamma_maha_5000"] - 0.05)
    claim("trap: true score 1.44, 136.5, 25.4%, 81%",
          "has a median of 1.44 in the Mahalanobis matched sample, but its 95th percentile is 136.5, and 25.4 per cent of pairs",
          v["to_med_maha"], ok=_agrees(v["to_med_maha"], "1.44") and _agrees(v["to_p95_maha"], "136.5")
          and _agrees(v["big_maha"], "25.4") and _agrees(v["big_mo_maha"], "81")
          and "81 per cent of the pairs with a ratio above ten" in prose)

    _, rows, _ = ms_table(s, "10.4")
    for r in rows:
        y_ = int(r[0])
        cell_(f"Table 10.4 {y_} years · odds", v[f"be_odds_{y_}"], money(r[1]))
        cell_(f"Table 10.4 {y_} years · odds lower", v[f"be_odds_{y_}_lo"], money(r[2]))
        cell_(f"Table 10.4 {y_} years · Mahalanobis", v[f"be_maha_{y_}"], money(r[3]))
        cell_(f"Table 10.4 {y_} years · Mahalanobis lower", v[f"be_maha_{y_}_lo"], money(r[4]))
    claim("odds $5,601 (se $241), Mahalanobis $6,640 (se $337)",
          "at $5,601 with a sandwich standard error of $241, and Mahalanobis matching, at $6,640 with a paired standard error of $337",
          v["policy_est_odds"], ok=_agrees(v["policy_est_odds"], "5,601") and _agrees(v["policy_se_odds"], "241")
          and _agrees(v["policy_est_maha"], "6,640") and _agrees(v["policy_se_maha"], "337"))
    p9 = results / "primary_estimates.csv"
    if p9.exists():
        e9 = pd.read_csv(p9).set_index("estimator").est
        att9 = [e9[k] for k in ("odds", "dr_att", "sub20", "sub20_reg", "match", "match_repl", "maha", "maha13")]
        claim("Table 9.1 range $4,921 to $6,640, Mahalanobis 1:3 $6,193", "range from $4,921 to $6,640. We take two of them",
              min(att9), ok=_agrees(min(att9), "4,921") and _agrees(max(att9), "6,640")
              and _agrees(e9["maha13"], "6,193") and "$6,193 for Mahalanobis matching with three controls" in prose)
    pw = results / "weighting_results.csv"
    if pw.exists():
        w6 = pd.read_csv(pw)
        g6 = w6[(w6.seed == 20260808) & (w6.score == "gbm") & (w6.trimmed == True)
                & (w6.estimand == "ATT") & (w6.estimator == "odds")].est
        claim("trimmed boosted odds weighting $6,209", "and $6,209 for odds weighting on the trimmed boosted score",
              float(g6.iloc[0]) if len(g6) else float("nan"), "6,209")
    claim("$5.6 million to $6.6 million per 1,000", "between $5.6 million and $6.6 million", v["policy_est_odds"],
          ok=_agrees(v["policy_est_odds"] / 1000, "5.6") and _agrees(v["policy_est_maha"] / 1000, "6.6"))
    claim("true ATT $6,408", "the true effect, $6,408", v["true_att"], "6,408")
    three = sum(1 / 1.03 ** k for k in range(3))
    claim("$766 is roughly $2,200 over three years", "by $766, or by roughly $2,200 over three years",
          v["bench_edu_3_bias"] * three, ok=2150 <= v["bench_edu_3_bias"] * three < 2250)
    claim("policy brief range $5,600 to $6,600", "earned about $5,600 to $6,600 more in 2019", v["policy_est_odds"],
          ok=round(v["policy_est_odds"], -2) == 5600 and round(v["policy_est_maha"], -2) == 6600)
    record(L, "the policy brief does not say significant",
           "significant" not in prose.split("A summary for a policy brief")[1].split("]],")[0].lower()
           if "A summary for a policy brief" in prose else False)


def report(strict: bool) -> int:
    w = max(len(c) for _, c, _, _ in RESULTS) + 2
    layer = None
    for lay, check, status, detail in RESULTS:
        if lay != layer:
            layer = lay
            print(f"\n{'=' * 78}\n{lay.upper()}\n{'=' * 78}")
        mark = {"PASS": "  ok  ", "FAIL": " FAIL ", "INFO": " info "}[status]
        print(f"[{mark}] {check.ljust(w)} {detail}")
    fails = [r for r in RESULTS if r[2] == "FAIL"]
    passes = [r for r in RESULTS if r[2] == "PASS"]
    print(f"\n{'=' * 78}")
    print(f"{len(passes)} passed · {len(fails)} failed · "
          f"{len(RESULTS) - len(passes) - len(fails)} informational")
    if fails:
        print("\nFAILURES")
        for lay, check, _, detail in fails:
            print(f"  [{lay}] {check}  —  {detail}")
    print("=" * 78)
    return 1 if (fails and strict) else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, default=Path("psm-book"))
    p.add_argument("--manuscript", type=Path, default=Path("ch02_content.js"))
    p.add_argument("--chapter", default=None,
                   help="chapter number; inferred from the manuscript filename")
    p.add_argument("--data", type=Path, default=None)
    p.add_argument("--tmp", type=Path, default=None,
                   help="scratch space for the reproducibility checks")
    p.add_argument("--results", type=Path, default=None,
                   help="Chapters 3 to 5: folder holding the multi-draw scripts' results "
                        "(default: <repo>/figures)")
    p.add_argument("--strict", action="store_true")
    p.add_argument("--skip-slow", action="store_true")
    a = p.parse_args()

    data = a.data or (a.repo / "plida_sim" / "plida_sim_a")
    if not data.exists():
        print(f"generating data at {data} ...", file=sys.stderr)
        subprocess.run([sys.executable, str(a.repo / "make_data.py"),
                        "--outdir", str(data), "--quiet"], check=True)

    if a.tmp is None:
        import atexit, shutil
        a.tmp = Path(tempfile.mkdtemp(prefix="psm-audit-"))
        atexit.register(shutil.rmtree, a.tmp, ignore_errors=True)
    tmpdir = a.tmp
    tmpdir.mkdir(parents=True, exist_ok=True)
    a.tmp = tmpdir
    layer_a(a.repo)
    d = layer_b(data)
    if not a.skip_slow:
        layer_b_reproducibility(a.repo, a.tmp)
    layer_c(d, data)
    vals = layer_d(a.repo, data)
    ch = a.chapter or (str(int(re.search(r'ch(\d\d)_content', a.manuscript.name).group(1)))
                       if re.search(r'ch(\d\d)_content', a.manuscript.name) else '2')
    layer_e(a.manuscript, a.repo, d, data, vals, ch)
    if ch == "3" and a.manuscript.exists():
        layer_e3(a.manuscript.read_text(), a.repo, data,
                 a.results or (a.repo / "figures"))
    if ch == "4" and a.manuscript.exists():
        layer_e4(a.manuscript.read_text(), a.repo, data,
                 a.results or (a.repo / "figures"))
    if ch == "6" and a.manuscript.exists():
        layer_e6(a.manuscript.read_text(), a.repo, data,
                 a.results or (a.repo / "figures"))
    if ch == "9" and a.manuscript.exists():
        layer_e9(a.manuscript.read_text(), a.repo, data,
                 a.results or (a.repo / "figures"))
    if ch == "5" and a.manuscript.exists():
        layer_e5_ch9(a.manuscript.read_text(), a.repo)
    if ch == "6" and a.manuscript.exists():
        layer_e6_ch9(a.manuscript.read_text(), a.repo)
    if ch == "8" and a.manuscript.exists():
        layer_e8(a.manuscript.read_text(), a.repo, data,
                 a.results or (a.repo / "figures"))
    if ch == "7" and a.manuscript.exists():
        layer_e7(a.manuscript.read_text(), a.repo, data,
                 a.results or (a.repo / "figures"))
    if ch == "5" and a.manuscript.exists():
        layer_e5(a.manuscript.read_text(), a.repo, data,
                 a.results or (a.repo / "figures"))
    if ch == "2" and a.manuscript.exists():
        layer_e2_truth(a.manuscript.read_text(), data)
    if ch == "1" and a.manuscript.exists():
        layer_e1(a.manuscript.read_text(), a.repo, data,
                 a.results or (a.repo / "figures"))
    if ch == "10" and a.manuscript.exists():
        layer_e10(a.manuscript.read_text(), a.repo, data,
                  a.results or (a.repo / "figures"))
    return report(a.strict)


if __name__ == "__main__":
    raise SystemExit(main())
