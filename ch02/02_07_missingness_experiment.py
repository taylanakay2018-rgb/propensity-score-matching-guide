#!/usr/bin/env python3
"""
Script 2.7 -- What each missing-data strategy actually costs
============================================================

Chapter 2, Section 2.7. Produces Table 2.7 and Figure 2.2.

Six strategies for handling missingness in the same covariate set, each carried
through an identical 1:1 nearest-neighbour match, each scored against known
truth -- and each repeated across five independent draws of the data.

The repetition is the point.  Run this on one dataset and you will see large,
confident-looking differences between imputation methods.  Most of them are
sampling noise.  The paired within-draw comparison at the end of the output
separates the real effects from the imaginary ones.

    python ch02_missingness_experiment.py

Runtime: about three minutes.
"""
import sys, warnings
import numpy as np, pandas as pd
from pathlib import Path
warnings.filterwarnings("ignore")
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from make_data import Config, generate
from validate_data import assemble
from sklearn.linear_model import LogisticRegression
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer, SimpleImputer
from sklearn.neighbors import NearestNeighbors
BASE=2016
def raw(df):
    X=pd.DataFrame(index=df.index)
    X["age"]=BASE-df["birth_year"]; X["female"]=(df["sex"]=="Female").astype(int)
    X["cob_other"]=(df["country_of_birth_group"]=="Other").astype(int)
    X["cob_mesc"]=(df["country_of_birth_group"]=="MESC").astype(int)
    X["log_inc_2015"]=np.log1p(df["inc_2015"]); X["log_inc_2016"]=np.log1p(df["inc_2016"])
    X["fn_2016"]=df["fn_2016"]; X["lts"]=(df["fn_2016"]>=20).astype(int)
    X["gp"]=df["gp_attendances"]; X["mh"]=df["mh_item_flag"]
    X["edu"]=df["highest_edu"].map({"<Year 12":0,"Year 12":1,"Cert III/IV":2,"Diploma":3,"Bachelor+":4})
    X["kids"]=df["dependent_children"]; X["lang"]=df["english_proficiency"].map({"Not well":1,"Well":0})
    X["remote"]=df["remoteness_area"].map({"Major Cities":0,"Inner Regional":1,"Outer Regional":2,"Remote+":3})
    X["seifa"]=df["seifa_irsd_decile"]
    for lv in ["Intensive","Full","Partial"]: X[f"mo_{lv.lower()}"]=(df["mutual_obligation"]==lv).astype(int)
    return X
rows=[]
import argparse as _ap
_p = _ap.ArgumentParser(description="Script 2.7 — what each missing-data strategy costs")
_p.add_argument("--datadir", type=Path, default=None,
                help="ignored: this script generates its own draws, by design")
_p.add_argument("--outdir", type=Path, default=Path(__file__).resolve().parent.parent / "figures")
_p.add_argument("--quick", action="store_true", help="one draw instead of five")
ARGS, _ = _p.parse_known_args()

# This script is the one exception to the --datadir contract: the whole point
# is to repeat the experiment on independent draws, so it generates them.
SEEDS = [20260808] if ARGS.quick else [20260808, 20260809, 20260810, 20260811, 20260812]

# --- Table 2.6: what is missing, and where it comes from --------------------
_fr0 = generate(Config(n=50_000, seed=SEEDS[0], quiet=True))
_fr0["truth"] = _fr0.pop("truth_parameters")
_d0 = assemble(_fr0)
_SRC = {"inc_2016": ("Salary and wages, 2016", "PIT", "Did not lodge a return"),
        "inc_2015": ("Salary and wages, 2015", "PIT", "Did not lodge a return"),
        "highest_edu": ("Highest education", "Census", "Census non-response"),
        "dependent_children": ("Dependent children", "Census", "Census non-response"),
        "english_proficiency": ("English proficiency", "Census", "Census non-response")}
print("\nTable 2.6 - missing values in the analysis file\n")
print(f"  {'Covariate':28s} {'Source':8s} {'Missing':>8s}  Why")
for _c, (_lab, _src, _why) in _SRC.items():
    print(f"  {_lab:28s} {_src:8s} {100 * _d0[_c].isna().mean():7.1f}%  {_why}")
_any = _d0[list(_SRC)].isna().any(axis=1).mean()
print(f"  {'Any of the above':28s} {'-':8s} {100 * _any:7.1f}%")
print("  The three Census items are missing together: the module is missing at")
print("  the person level, so it is one mechanism rather than three.")

for seed in SEEDS:
    fr=generate(Config(n=50_000,seed=seed,quiet=True)); fr["truth"]=fr.pop("truth_parameters")
    df=assemble(fr); D=df.treated.values; tau=df.tau_i.values; y=np.where(D==1,df.y1,df.y0)
    ATT=tau[D==1].mean(); X0=raw(df); miss=[c for c in X0.columns if X0[c].isna().any()]
    def est(X,keep):
        Dk,yk,tk=D[keep],y[keep],tau[keep]; Xs=(X-X.mean())/X.std().replace(0,1)
        ps=LogisticRegression(max_iter=4000,C=1e6).fit(Xs,Dk).predict_proba(Xs)[:,1]
        lo=np.log(ps/(1-ps)); t=np.where(Dk==1)[0]; c=np.where(Dk==0)[0]
        nn=NearestNeighbors(n_neighbors=1).fit(lo[c].reshape(-1,1)); dd,ii=nn.kneighbors(lo[t].reshape(-1,1))
        k=dd.ravel()<=0.1*lo.std(); mt,mc=t[k],c[ii.ravel()[k]]
        return (yk[mt]-yk[mc]).mean(), tk[mt].mean()
    allr=np.ones(len(df),bool); cc=X0.notna().all(axis=1).values
    med=pd.DataFrame(SimpleImputer(strategy="median").fit_transform(X0),columns=X0.columns,index=X0.index)
    it=pd.DataFrame(IterativeImputer(max_iter=10,random_state=0).fit_transform(X0),columns=X0.columns,index=X0.index)
    ind=X0[miss].isna().astype(int).add_suffix("_missing")
    r={"seed":seed}
    for nm,X,kp in [("1 complete case",X0[cc],cc),
                    ("2 drop columns",X0.drop(columns=miss),allr),
                    ("3 median",med,allr),
                    ("4 median+ind",pd.concat([med,ind],axis=1),allr),
                    ("5 iterative",it,allr),
                    ("6 iterative+ind",pd.concat([it,ind],axis=1),allr)]:
        e,l=est(X,kp); r[nm]=100*(e-l)/l
    best=pd.concat([it,ind],axis=1)
    for nm,cols in [("enc 3 dummies",["mo_intensive","mo_full","mo_partial"]),
                    ("enc 2 dummies",["mo_intensive","mo_full"]),
                    ("enc 1 dummy",["mo_intensive"])]:
        k=[c for c in best.columns if not c.startswith("mo_")]+cols
        e,l=est(best[k],allr); r[nm]=100*(e-l)/l
    rows.append(r); print("seed",seed,"done",file=sys.stderr)
t=pd.DataFrame(rows).set_index("seed")
print("\nTable 2.7 - bias (%) by missing-data strategy, five draws\n"); print(t.iloc[:,:6].round(1).to_string())
print("\n"+pd.DataFrame({"mean":t.iloc[:,:6].mean(),"sd":t.iloc[:,:6].std()}).round(1).to_string())
print("\n\nPaired within-draw differences vs '4 median+ind' (removes draw noise)\n")
dif=t.iloc[:,:6].sub(t["4 median+ind"],axis=0).drop(columns=["4 median+ind"])
print(pd.DataFrame({"mean diff":dif.mean(),"sd of diff":dif.std()}).round(1).to_string())
print("\n\nEncoding, paired vs 3 dummies\n")
e=t[["enc 3 dummies","enc 2 dummies","enc 1 dummy"]]
d2=e.sub(e["enc 3 dummies"],axis=0).drop(columns=["enc 3 dummies"])
print(pd.DataFrame({"mean":e.mean(),"sd":e.std()}).round(1).to_string())
print("\npaired diff vs 3 dummies:"); print(pd.DataFrame({"mean diff":d2.mean(),"sd of diff":d2.std()}).round(1).to_string())


# ---------------------------------------------------------------------------
# Figure 2.2 -- the diagnosis beside the consequence
# ---------------------------------------------------------------------------
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

plt.rcParams.update({
    "font.family": "serif", "font.size": 9, "axes.linewidth": 0.8,
    "axes.labelsize": 8.5, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5, "legend.frameon": False,
    "savefig.dpi": 300, "savefig.bbox": "tight", "savefig.facecolor": "white",
})

def _panel(ax, letter):
    ax.text(-0.02, 1.06, f"({letter})", transform=ax.transAxes,
            fontsize=10, fontweight="bold", va="bottom", ha="right")

if len(SEEDS) < 5:
    print("\n--quick: skipping Figure 2.2, which needs all five draws.")
    sys.exit(0)

fr = generate(Config(n=50_000, seed=SEEDS[0], quiet=True)); fr["truth"] = fr.pop("truth_parameters")
df0 = assemble(fr)
absent = df0["inc_2016"].isna().values
feats = {
    "Fortnights on payment": df0["fn_2016"].values.astype(float),
    "Commenced programme": df0["treated"].values.astype(float),
    "Outer regional / remote": df0["remoteness_area"].isin(["Outer Regional", "Remote+"]).astype(float).values,
    "Long-term support": (df0["fn_2016"] >= 20).astype(float).values,
    "Mental health item": df0["mh_item_flag"].values.astype(float),
    "GP attendances": df0["gp_attendances"].values.astype(float),
    "Age": (2016 - df0["birth_year"]).values.astype(float),
}
prof = pd.DataFrame([{"feature": k,
                      "smd": (v[absent].mean() - v[~absent].mean())
                             / np.sqrt((v[absent].var() + v[~absent].var()) / 2)}
                     for k, v in feats.items()]).sort_values("smd")

fig, (axa, axb) = plt.subplots(1, 2, figsize=(6.9, 3.4),
                               gridspec_kw={"width_ratios": [1.0, 1.12]})
yy = np.arange(len(prof))
axa.barh(yy, prof["smd"], height=0.6, facecolor="white", edgecolor="black",
         linewidth=0.8, hatch="////")
axa.axvline(0, color="black", linewidth=0.8)
for x in (-0.1, 0.1):
    axa.axvline(x, color="black", linewidth=0.7, linestyle=(0, (4, 3)))
axa.set_yticks(yy); axa.set_yticklabels(prof["feature"])
axa.set_xlabel("Standardised difference:\nno 2016 tax record versus has one")
axa.set_xlim(-0.45, 0.82)
for sp in ("top", "right"): axa.spines[sp].set_visible(False)
_panel(axa, "a")

# The labels as they appear in the book's Figure 2.2.
LABELS = {
    "1 complete case":  "Complete case\n(listwise deletion)",
    "2 drop columns":   "Drop every column\nthat has any missing",
    "3 median":         "Median imputation",
    "4 median+ind":     "Median imputation\n+ indicators",
    "5 iterative":      "Iterative imputation",
    "6 iterative+ind":  "Iterative imputation\n+ indicators",
}
order = t.iloc[:, :6].mean().sort_values().index
yy = np.arange(len(order))
for i, name in enumerate(order):
    vals = t[name].values
    axb.plot([vals.min(), vals.max()], [i, i], color="black", linewidth=0.7, zorder=1)
    axb.scatter(vals, [i] * len(vals), s=15, facecolors="white", edgecolors="black",
                linewidths=0.7, zorder=2)
    axb.scatter([vals.mean()], [i], s=34, marker="D", facecolors="black",
                edgecolors="black", zorder=3)
axb.axvline(0, color="black", linewidth=0.9)
axb.set_yticks(yy)
axb.set_yticklabels([LABELS[n] for n in order], fontsize=7)
axb.set_xlabel("Bias in the estimated ATT (%),\nfive independent draws")
axb.set_xlim(-84, 24)
for sp in ("top", "right"): axb.spines[sp].set_visible(False)
axb.scatter([], [], s=15, facecolors="white", edgecolors="black", label="one draw")
axb.scatter([], [], s=34, marker="D", facecolors="black", edgecolors="black", label="mean of five")
axb.legend(loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=2, fontsize=7,
           handletextpad=0.3, columnspacing=1.2)
_panel(axb, "b")

fig.subplots_adjust(wspace=0.55)
outdir = ARGS.outdir
outdir.mkdir(parents=True, exist_ok=True)
for ext, kw in [("tif", dict(format="tiff", pil_kwargs={"compression": "tiff_lzw"})), ("png", {})]:
    fig.savefig(outdir / f"figure_2_2_missing_data.{ext}", dpi=300, **kw)
plt.close(fig)
print(f"\nwrote figure_2_2_missing_data.tif and .png to {outdir}")
