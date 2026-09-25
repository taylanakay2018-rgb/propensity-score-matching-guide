#!/usr/bin/env python3
"""
Script 2.2 — Coverage and units
================================
Chapter 2, Sections 2.5.1 and 2.6.5. Produces Figure 2.1.

Panel (a) plots the share of persons with a record in each module by year.
Panel (b) contrasts nominal earnings with earnings deflated to constant 2019
dollars. Both panels are monochrome line art at 300 dpi.

    python ch02/02_02_coverage_and_units.py
"""
import sys; sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from _common import cli, load, banner, YEARS
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "axes.linewidth": 0.8,
    "axes.labelsize": 8.5, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5, "legend.frameon": False,
    "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.facecolor": "white",
})

def panel_label(ax, letter):
    ax.text(-0.02, 1.06, f"({letter})", transform=ax.transAxes,
            fontsize=10, fontweight="bold", va="bottom", ha="right")

def main():
    a = cli(__doc__)
    d = load(a.datadir)
    n = len(d["spine_scoping"])
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(6.9, 3.0),
                                   gridspec_kw={"width_ratios": [1.15, 1.0]})

    mods = [("Personal income tax", "pit_income"), ("Income support", "domino_payments"),
            ("Health (MBS/PBS)", "mbs_pbs_health"), ("Locations", "core_locations")]
    cov = pd.DataFrame({name: [d[f].query("ref_year == @y")["person_id"].nunique() / n * 100
                               for y in YEARS] for name, f in mods}, index=YEARS)
    for i, (name, mk, ls) in enumerate(zip(cov.columns, "os^D", ["-", "--", "-.", ":"])):
        axa.plot(cov.index, cov[name], color="black", linestyle=ls, marker=mk,
                 markersize=4, markerfacecolor="white", linewidth=1.0, label=name)
    axa.axvline(2016.5, color="black", linewidth=0.7, alpha=0.5)
    axa.text(2016.6, 96, "treatment\nyear", fontsize=7, style="italic", va="top")
    axa.set_ylim(8, 108); axa.set_xticks(YEARS)
    axa.set_ylabel("Persons with a record that year (%)"); axa.set_xlabel("Reference year")
    axa.legend(loc="lower left", fontsize=7, bbox_to_anchor=(-0.02, -0.02))
    for s in ("top", "right"): axa.spines[s].set_visible(False)
    panel_label(axa, "a")

    idx = d["reference_indices"].set_index("ref_year"); pit = d["pit_income"]
    nominal = [pit.query("ref_year == @y")["salary_wages_nominal"].mean() for y in YEARS]
    real = [nominal[i] / (idx.loc[y, "cpi_index"] / 100.0) for i, y in enumerate(YEARS)]
    axb.plot(YEARS, np.array(nominal)/1000, color="black", linestyle="--", marker="o",
             markersize=4, markerfacecolor="white", linewidth=1.0, label="As recorded (nominal)")
    axb.plot(YEARS, np.array(real)/1000, color="black", linestyle="-", marker="s",
             markersize=4, markerfacecolor="black", linewidth=1.2, label="Deflated (constant 2019 AUD)")
    axb.annotate("", xy=(2014, real[0]/1000), xytext=(2014, nominal[0]/1000),
                 arrowprops=dict(arrowstyle="<->", linewidth=0.8, color="black"))
    axb.text(2014.15, (real[0]+nominal[0])/2000,
             f"{100*(real[0]-nominal[0])/real[0]:.0f}%", fontsize=7.5, va="center")
    lo, hi = min(min(nominal), min(real))/1000, max(max(nominal), max(real))/1000
    axb.set_ylim(lo - 0.30*(hi-lo), hi + 0.05*(hi-lo)); axb.set_xticks(YEARS)
    axb.set_ylabel("Mean salary and wages ($000)"); axb.set_xlabel("Reference year")
    axb.legend(loc="lower left", fontsize=7, bbox_to_anchor=(-0.02, -0.02))
    for s in ("top", "right"): axb.spines[s].set_visible(False)
    panel_label(axb, "b")

    fig.subplots_adjust(wspace=0.32)
    a.outdir.mkdir(parents=True, exist_ok=True)
    for ext, kw in [("tif", dict(format="tiff", pil_kwargs={"compression": "tiff_lzw"})), ("png", {})]:
        fig.savefig(a.outdir / f"figure_2_1_the_raw_data.{ext}", dpi=300, **kw)
    plt.close(fig)
    print(f"wrote figure_2_1_the_raw_data.tif and .png to {a.outdir}")

    banner("Figure 2.1(a) — coverage by module and year (%)")
    print(cov.round(1).to_string())
    banner("Figure 2.1(b) — the cost of not deflating")
    for i, y in enumerate(YEARS):
        print(f"  {y}  nominal ${nominal[i]:>9,.0f}   real ${real[i]:>9,.0f}   "
              f"understated by {100*(real[i]-nominal[i])/real[i]:4.1f}%")

if __name__ == "__main__":
    main()
