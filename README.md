# The Applied Researcher's Guide to Propensity Score Matching

Companion code and data for *The Applied Researcher's Guide to Propensity Score
Matching: Python Scripts for Data Preparation and Robust Causal Effects*
(Taylan Akay, Taylor & Francis / CRC Press).

Every script the book refers to lives here. Every figure and table in the book
is produced by one of them, and the caption says which.

---

## Start here

```bash
git clone https://github.com/taylanakay2018-rgb/propensity-score-matching-guide.git
cd propensity-score-matching-guide
pip install -r requirements.txt     # or: conda env create -f environment.yml

python make_data.py --outdir plida_sim/plida_sim_a     # ~5 seconds
python ch02/02_01_load_modules.py
```

Chapters 3 onwards start from the analysis file Chapter 2 builds, so build that
first. Every script reads `plida_sim/plida_sim_a` unless given `--datadir`:

```bash
python ch02/02_05_link_modules.py
python ch02/02_06_reshape_panel.py
python ch03/03_02_estimate_logit.py
```

The dataset is generated rather than downloaded. It takes five seconds, the
output is byte-identical on every machine, and it means the repository stays
small enough to clone quickly.

If you cannot install packages on your machine, which is common on
government and corporate workstations, each chapter below has an **Open in
Colab** badge. The notebook clones this repository, installs the same pinned
versions, generates the data and runs the chapter's scripts in order, in a
browser. `causalml` is not installed there; it is optional, and every exercise
that uses it has a scikit-learn fallback.

For the end-of-chapter exercises, generate the second variant:

```bash
python make_data.py --variant B --outdir plida_sim/plida_sim_b
```

---

## What is here

| Path | What it is |
| --- | --- |
| `make_data.py` | Generates PLIDA-SIM. Seeded, reproducible, ~5 s |
| `validate_data.py` | Checks the generated data against every benchmark in the book |
| `stability.py` | Estimator bias across independent draws (Chapters 5 and 9), ~2 min |
| `forward_dependencies.py` | Checks the analysis file supports the chapters not yet written, ~1 min |
| `audit.py` | Holds each chapter to the data: every table cell, number and cross-reference |
| `requirements.txt`, `environment.yml` | The pinned environment, for pip or conda |
| `colab/` | One notebook per chapter, built by `make_notebooks.py` from the tables below |
| `ch01/` to `ch10/` | The chapter scripts, listed below |
| `results/` | Committed results of runs too long for continuous integration (Chapter 9's 200 draws) |
| `manuscript/` | The chapter text, which `audit.py` reads |
| `figures/` | Where the scripts write figures |
| `plida_sim/` | Where the generator writes data (git-ignored) |

The tables below are the script tables printed at the end of each chapter.
`audit.py` checks that they still agree.

### Chapter 1 — Overview of Propensity Score Analysis in Observational Studies

[![Open Chapter 1 in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/taylanakay2018-rgb/propensity-score-matching-guide/blob/main/colab/ch01.ipynb)

| Script | File | Produces | Runtime |
| --- | --- | --- | --- |
| 1.1 | `ch01/01_01_overview.py` | Table 1.1; Figure 1.1; the figures of Sections 1.2 and 1.6 | 30 s |

Script 1.1 reads the analysis file that Scripts 2.5 and 2.6 build, so run those first.

### Chapter 2 — Preparing Observational Data

[![Open Chapter 2 in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/taylanakay2018-rgb/propensity-score-matching-guide/blob/main/colab/ch02.ipynb)

| Script | File | Produces | Runtime |
| --- | --- | --- | --- |
| 2.1 | `ch02/02_01_load_modules.py` | The nine modules profiled; Table 2.3 | 5 s |
| 2.2 | `ch02/02_02_coverage_and_units.py` | Figure 2.1 | 10 s |
| 2.3 | `ch02/02_03_plida_sim_properties.py` | The generator summary in 2.3 | 5 s |
| 2.4 | `ch02/02_04_covariate_sets.py` | Tables 2.1 and 2.2 | 40 s (4 min with --placement) |
| 2.5 | `ch02/02_05_link_modules.py` | The linked file; Table 2.4 | 20 s |
| 2.6 | `ch02/02_06_reshape_panel.py` | The analysis file; Table 2.5 | 20 s |
| 2.7 | `ch02/02_07_missingness_experiment.py` | Tables 2.6 and 2.7; Figure 2.2 | 3 min |
| 2.8 | `ch02/02_08_attrition.py` | Table 2.8 | 15 s |
| 2.9 | `ch02/02_09_score_against_truth.py` | Table 2.9; the scoring used throughout | 10 s |

### Chapter 3 — Building the Propensity Score Analysis

[![Open Chapter 3 in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/taylanakay2018-rgb/propensity-score-matching-guide/blob/main/colab/ch03.ipynb)

| Script | File | Produces | Runtime |
| --- | --- | --- | --- |
| 3.1 | `ch03/03_01_covariate_sets.py` | Table 3.1; the design matrix | 10 s |
| 3.2 | `ch03/03_02_estimate_logit.py` | Table 3.2; the logistic score | 15 s |
| 3.3 | `ch03/03_03_estimate_gbm.py` | The boosted score | 30 s |
| 3.4 | `ch03/03_04_compare_estimators.py` | Table 3.4, primary-dataset rows | 40 s |
| 3.5 | `ch03/03_05_specifications.py` | Table 3.3; Table 3.4, five-draw rows; Figure 3.1 | 4 min |
| 3.6 | `ch03/03_06_diagnose_score.py` | Table 3.6; Figure 3.2 | 20 s |
| 3.7 | `ch03/03_07_near_instrument.py` | Table 3.5 | 3 min |

### Chapter 4 — Initial Dataset Trimming

[![Open Chapter 4 in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/taylanakay2018-rgb/propensity-score-matching-guide/blob/main/colab/ch04.ipynb)

| Script | File | Produces | Runtime |
| --- | --- | --- | --- |
| 4.1 | `ch04/04_01_assess_overlap.py` | Table 4.1; the common support region | 15 s |
| 4.2 | `ch04/04_02_trimming_rules.py` | Table 4.2; the seven trimmed samples | 20 s |
| 4.3 | `ch04/04_03_compare_rules.py` | Tables 4.3 and 4.4; Figure 4.1 | 5 min |
| 4.4 | `ch04/04_04_who_is_removed.py` | Table 4.5 | 15 s |

### Chapter 5 — Creating Balanced Datasets with Propensity Score Matching

[![Open Chapter 5 in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/taylanakay2018-rgb/propensity-score-matching-guide/blob/main/colab/ch05.ipynb)

| Script | File | Produces | Runtime |
| --- | --- | --- | --- |
| 5.1 | `ch05/05_01_match_basics.py` | Table 5.1; a first matched sample | 20 s |
| 5.2 | `ch05/05_02_match_variants.py` | The nine matched datasets | 40 s |
| 5.3 | `ch05/05_03_compare_variants.py` | Tables 5.2 to 5.7; Figure 5.1; the checks of Sections 5.4 and 5.6 | 9 min |
| 5.4 | `ch05/05_04_reuse_and_balance.py` | Table 5.8; Figure 5.2 | 30 s |

### Chapter 6 — Creating Balanced Datasets with Inverse Probability Weighting

[![Open Chapter 6 in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/taylanakay2018-rgb/propensity-score-matching-guide/blob/main/colab/ch06.ipynb)

| Script | File | Produces | Runtime |
| --- | --- | --- | --- |
| 6.1 | `ch06/06_01_build_weights.py` | Table 6.1; the weights | 20 s |
| 6.2 | `ch06/06_02_compare_weighting.py` | Tables 6.2 to 6.6 and 6.8; Figures 6.1 and 6.2 | 4 min |
| 6.3 | `ch06/06_03_right_for_the_wrong_reason.py` | Table 6.7 | 1 min |

### Chapter 7 — Stratification, Subclassification and Other Approaches

[![Open Chapter 7 in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/taylanakay2018-rgb/propensity-score-matching-guide/blob/main/colab/ch07.ipynb)

| Script | File | Produces | Runtime |
| --- | --- | --- | --- |
| 7.1 | `ch07/07_01_form_strata.py` | Tables 7.1 and 7.2; the cell counts of Section 7.4 | 5 s |
| 7.2 | `ch07/07_02_compare_strata.py` | Tables 7.3 to 7.5 and 7.8; the figures of Section 7.7 | 5 min |
| 7.3 | `ch07/07_03_spline_on_score.py` | Tables 7.6 and 7.7 | 4 min |

### Chapter 8 — Assessing Covariate Balance in the New Datasets

[![Open Chapter 8 in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/taylanakay2018-rgb/propensity-score-matching-guide/blob/main/colab/ch08.ipynb)

| Script | File | Produces | Runtime |
| --- | --- | --- | --- |
| 8.1 | `ch08/08_01_balance_table.py` | Tables 8.1 to 8.3 | 10 s |
| 8.2 | `ch08/08_02_diagnostics_across_draws.py` | Tables 8.4 to 8.7; the identity of Section 8.2 | 5 min |

### Chapter 9 — Causal Effect Estimation and Correct Variance

[![Open Chapter 9 in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/taylanakay2018-rgb/propensity-score-matching-guide/blob/main/colab/ch09.ipynb)

| Script | File | Produces | Runtime |
| --- | --- | --- | --- |
| 9.1 | `ch09/09_01_estimate_primary.py` | Table 9.1; the figures of Sections 9.3 and 9.7 | 6 min |
| 9.2 | `ch09/09_02_standard_errors_across_draws.py` | Tables 9.2 to 9.5; Figure 9.1 | 25 min |

Script 9.2's tables come from `results/ch09_standard_errors_200.csv`, the committed
output of the full run (200 draws, the bootstrap on the first 40; about three hours
on two cores). By default the script reruns the first 40 draws and confirms they
reproduce the committed rows. To repeat the full run:
`python ch09/09_02_standard_errors_across_draws.py --draws 200 --boot-draws 40 --commit`.

### Chapter 10 — Sensitivity, Interpretation and Policy Recommendations

[![Open Chapter 10 in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/taylanakay2018-rgb/propensity-score-matching-guide/blob/main/colab/ch10.ipynb)

| Script | File | Produces | Runtime |
| --- | --- | --- | --- |
| 10.1 | `ch10/10_01_sources_of_bias.py` | Tables 10.1 and 10.5; the figures of Sections 10.2.1 and 10.4.3 | 20 min |
| 10.2 | `ch10/10_02_sensitivity.py` | Tables 10.2, 10.3 and 10.4; Figure 10.1 | 1 min |

Script 10.2 writes the numbers it prints to `figures/sensitivity_primary.csv`,
from which the audit checks the chapter.

Within each chapter, run the scripts in order. Scripts 2.6 onwards depend on
the file Script 2.5 writes, and Chapters 1 and 3 to 10 depend on the analysis file
Script 2.6 writes. Scripts that repeat an experiment across draws accept
`--quick` for a single draw; Scripts 5.3, 6.2, 6.3, 7.2, 7.3, 8.2, 9.2
and 10.1 generate their own draws and ignore `--datadir`.

---

## About the data

> **PLIDA-SIM is entirely simulated.** It is not PLIDA data, not derived from
> PLIDA data, and no PLIDA record contributed to it. It imitates the structure
> of the ABS Person Level Integrated Data Asset so that the workflow transfers,
> but every value is generated from equations in `make_data.py`. Parameter
> values were chosen for pedagogical clarity, not to reproduce any real
> Australian estimate. **No result from this dataset is evidence about any
> Australian programme.**

Two departures from realism are worth knowing about before you start. The
programme effect is larger than real employment programmes achieve — around
15% of the control mean — so that every diagnostic in the book is legible.
And the record linkage is perfect, which real probabilistic linkage never is.
Section 2.3.2 of the book discusses both.

### `plida_sim/*/truth/` — do not join this into an analysis

`truth_parameters.csv` holds both potential outcomes for every person. It
exists only because this is a teaching dataset. Use it at the *end* of an
exercise, to score an estimate you produced without it.

The book's scripts use it for exactly that: to score a method against the
known effect, never to produce the estimate being scored. They load it only
when asked (`with_truth=True`, off by default). The Chapter 2 scripts keep it
as a separate table rather than joining it; from Chapter 3 onwards it is
joined under underscored names (`_y0`, `_y1`, `_tau_i`) so that no truth
column can enter a model by accident. Scripts that repeat an experiment
across draws generate each draw, truth included, in memory.

---

## Reproducibility

A single master seed is spawned into ten independent per-module streams via
`numpy.random.SeedSequence`, so a module can be re-parameterised without
disturbing any other. Output is byte-identical across runs on the same
platform and version set, and `manifest.json` stamps the dataset version and
seed alongside every build.

`validate_data.py --strict` reproduces every benchmark number quoted in the
book and exits non-zero if any has moved. On every commit, continuous
integration runs it, every chapter script, `stability.py`,
`forward_dependencies.py --strict`, and `audit.py --strict` on each chapter —
see `.github/workflows/ci.yml`. To run the Chapter 5 audit yourself, run
Script 5.3 first, in full: the audit reads the six-draw results it writes.

```bash
python ch05/05_03_compare_variants.py
python audit.py --repo . --manuscript manuscript/ch05_content.js --strict
```

Tolerances on the estimator checks are wide, at roughly two standard
deviations of the bias measured across six draws by `stability.py`. They are
wide because the estimators genuinely are, which is a finding the book makes
much of rather than an admission.

---

## Errata and corrections

Please open an issue if a script does not run, a number does not match the
book, or a result looks wrong. Corrections will be listed here.

## Licence

Code MIT; data CC BY 4.0. See `LICENCE`.
