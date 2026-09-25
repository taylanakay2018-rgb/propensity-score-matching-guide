#!/usr/bin/env python3
"""
Build the Colab notebooks, one per chapter
===========================================
Each notebook clones this repository, installs the required packages at the
versions in requirements.txt, generates PLIDA-SIM, and runs the chapter's
scripts in order. Nothing in a notebook is written by hand: the script list
and what each script produces are read from the README's chapter tables,
which audit.py holds to the chapters' own script tables. audit.py also
rebuilds the notebooks in memory and fails if a committed notebook differs,
so a chapter cannot gain a script that its notebook does not run.

    python colab/make_notebooks.py

The notebooks exist for readers who cannot install the environment locally,
most often behind a locked-down workstation. causalml is not installed: it is
optional, and every exercise that uses it has a scikit-learn fallback.

REPO is the GitHub address the badges and notebooks point to. Until the
repository is published it holds a placeholder, which audit.py reports.
Publishing is then one command:

    python colab/make_notebooks.py --repo OWNER/NAME
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER = "OWNER/psm-book"
CORE = ("numpy", "pandas", "scikit-learn", "scipy",
        "matplotlib", "seaborn", "statsmodels")
# Chapters 3 onwards read the analysis file that these two scripts build.
PREREQ = ["ch02/02_05_link_modules.py", "ch02/02_06_reshape_panel.py"]


def current_repo(readme: str) -> str:
    m = re.search(r"git clone https://github\.com/([\w.-]+/[\w.-]+?)\.git", readme)
    return m.group(1) if m else PLACEHOLDER


def chapters(readme: str) -> dict:
    """{'02': (title, [(number, file, produces, runtime), ...]), ...}"""
    out = {}
    for m in re.finditer(r"^### Chapter (\d{1,2}) — (.+?)\n(.*?)(?=\n### |\n---)",
                         readme, re.S | re.M):
        rows = re.findall(r"^\| (\d{1,2}\.\d+) \| `(ch[01]\d/[^`]+\.py)` \| (.*?) \| (.*?) \|$",
                          m.group(3), re.M)
        out[f"{int(m.group(1)):02d}"] = (m.group(2), rows)
    return out


def md(*lines):
    return {"cell_type": "markdown", "metadata": {}, "source": "\n".join(lines)}


def code(*lines):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": "\n".join(lines)}


def notebook(ch: str, title: str, rows: list, repo: str) -> dict:
    name = repo.split("/")[1]
    n = int(ch)
    cells = [
        md(f"# Chapter {n} — {title}",
           "",
           "*The Applied Researcher's Guide to Propensity Score Matching*, companion code.",
           "",
           "This notebook runs the chapter's scripts exactly as the book does. It clones",
           "the repository, installs the pinned packages, generates PLIDA-SIM (about five",
           "seconds), and runs each script in order. Every table and figure the chapter",
           "prints comes from one of the cells below; figures are written to `figures/`.",
           "",
           "PLIDA-SIM is entirely simulated. No result from it is evidence about any",
           "Australian programme."),
        code(f"!git clone -q https://github.com/{repo}.git",
             f"%cd {name}"),
        md("The packages are installed at the versions the book was verified with. Each",
           "script runs in its own process, so the new versions are used without",
           "restarting the runtime. causalml is optional and is not installed here."),
        code("!pip install -q $(grep -E '^(" + "|".join(CORE) + ")==' requirements.txt)"),
        code("!python make_data.py --outdir plida_sim/plida_sim_a --quiet",
             "!python validate_data.py --datadir plida_sim/plida_sim_a --strict"),
    ]
    if ch != "02":
        cells += [
            md("Every chapter but Chapter 2 starts from the analysis file Chapter 2 builds."),
            code(*[f"!python {f} > /dev/null" for f in PREREQ]),
        ]
    for num, f, prod, rt in rows:
        cells += [md(f"## Script {num}", "", f"Produces: {prod}. Runtime: about {rt}."),
                  code(f"!python {f}")]
    if any("Figure" in prod for _, _, prod, _ in rows):      # Chapter 7 has none
        cells += _figure_cells(n)
    for i, c in enumerate(cells):          # nbformat 4.5 requires a stable id per cell
        c["id"] = f"cell-{i:02d}"
    return {"cells": cells,
            "metadata": {"colab": {"name": f"ch{ch}.ipynb", "provenance": []},
                         "kernelspec": {"display_name": "Python 3", "name": "python3"},
                         "language_info": {"name": "python"}},
            "nbformat": 4, "nbformat_minor": 5}


def _figure_cells(n):
    return [md("## Show the figures",
               "",
               "Scripts write each figure as a PNG for the screen and a TIF for print."),
            code("from IPython.display import Image, display",
                 "from pathlib import Path",
                 f"for f in sorted(Path('figures').glob('figure_{n}_*.png')):",
                 "    print(f.name)",
                 "    display(Image(filename=str(f)))")]


def render(nb: dict) -> str:
    return json.dumps(nb, indent=1, ensure_ascii=False) + "\n"


def build(readme: str, repo: str | None = None) -> dict:
    """{'colab/ch02.ipynb': text, ...}. audit.py calls this too."""
    repo = repo or current_repo(readme)
    return {f"colab/ch{ch}.ipynb": render(notebook(ch, t, rows, repo))
            for ch, (t, rows) in chapters(readme).items()}


def badge(ch: str, repo: str) -> str:
    return (f"[![Open Chapter {int(ch)} in Colab](https://colab.research.google.com/assets/colab-badge.svg)]"
            f"(https://colab.research.google.com/github/{repo}/blob/main/colab/ch{ch}.ipynb)")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", help="GitHub OWNER/NAME; rewrites the README too")
    a = p.parse_args()
    rm = ROOT / "README.md"
    readme = rm.read_text()
    old = current_repo(readme)
    if a.repo and a.repo != old:
        readme = readme.replace(old, a.repo).replace(
            f"cd {old.split('/')[1]}\n", f"cd {a.repo.split('/')[1]}\n")
        rm.write_text(readme)
        print(f"README now points at {a.repo}")
    for rel, txt in build(readme).items():
        (ROOT / rel).write_text(txt)
        print(f"wrote {rel}")


if __name__ == "__main__":
    main()
