#!/usr/bin/env python3
"""Bias of each estimator across independent draws of the data-generating process.

Produces the exhibit behind the claim that estimator *variance* dominates
estimator *choice* in this dataset. Also the source of the tolerance bands in
validate_data.py, which are set at roughly two standard deviations of the bias
measured here.

    python stability.py

Runtime: about two minutes for six draws of 50,000 persons.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from make_data import Config, generate
from validate_data import assemble, design_matrix
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import SplineTransformer

rows=[]
for seed in [20260808, 20260809, 20260810, 20260811, 20260812, 20260813]:
    fr = generate(Config(n=50_000, seed=seed, quiet=True))
    d = {k: v for k, v in fr.items()}; d["truth"]=d.pop("truth_parameters")
    df = assemble(d)
    X = design_matrix(df); Xs=(X-X.mean())/X.std()
    D=df.treated.values; tau=df.tau_i.values; y=np.where(D==1,df.y1,df.y0)
    ps=LogisticRegression(max_iter=4000,C=1e6).fit(Xs,D).predict_proba(Xs)[:,1]
    sup=(ps>0.05)&(ps<0.95); r={"seed":seed}

    lo=np.log(ps/(1-ps)); t=np.where(D==1)[0]; c=np.where(D==0)[0]
    nn=NearestNeighbors(n_neighbors=1).fit(lo[c].reshape(-1,1))
    dd,ii=nn.kneighbors(lo[t].reshape(-1,1)); k=dd.ravel()<=0.1*lo.std()
    mt,mc=t[k],c[ii.ravel()[k]]
    r["NN match .1SD"]=100*((y[mt]-y[mc]).mean()-tau[mt].mean())/tau[mt].mean()

    w=np.where(D==1,D.mean()/ps,(1-D.mean())/(1-ps))
    e=(np.sum(w*D*y)/np.sum(w*D))-(np.sum(w*(1-D)*y)/np.sum(w*(1-D)))
    r["IPTW untrim"]=100*(e-tau.mean())/tau.mean()
    ws=np.where(D[sup]==1,D[sup].mean()/ps[sup],(1-D[sup].mean())/(1-ps[sup])); ds,ys=D[sup],y[sup]
    e=(np.sum(ws*ds*ys)/np.sum(ws*ds))-(np.sum(ws*(1-ds)*ys)/np.sum(ws*(1-ds)))
    r["IPTW trim"]=100*(e-tau[sup].mean())/tau[sup].mean()

    g=dict(n_estimators=250,max_depth=3,learning_rate=0.05,random_state=1)
    m1=GradientBoostingRegressor(**g).fit(X[D==1],y[D==1]).predict(X)
    m0=GradientBoostingRegressor(**g).fit(X[D==0],y[D==0]).predict(X)
    sc=m1-m0+D*(y-m1)/ps-(1-D)*(y-m0)/(1-ps)
    r["AIPW trim"]=100*(sc[sup].mean()-tau[sup].mean())/tau[sup].mean()

    qs=np.unique(np.quantile(ps[D==1],np.linspace(0,1,21))); qs[0],qs[-1]=0,1
    sub=pd.cut(ps,qs,labels=False,include_lowest=True); num=den=tn=0
    for s in np.unique(sub[~pd.isna(sub)]):
        m=sub==s
        if (m&(D==1)).sum()>5 and (m&(D==0)).sum()>5:
            nk=(m&(D==1)).sum(); num+=nk*(y[m&(D==1)].mean()-y[m&(D==0)].mean())
            tn+=nk*tau[m&(D==1)].mean(); den+=nk
    r["Subclass 20"]=100*(num-tn)/tn

    B=SplineTransformer(n_knots=25,degree=3).fit_transform(ps.reshape(-1,1)); Z=np.hstack([B,Xs.values])
    f1=Ridge(1.0).fit(Z[D==1],y[D==1]).predict(Z); f0=Ridge(1.0).fit(Z[D==0],y[D==0]).predict(Z)
    r["Spline trim"]=100*((f1-f0)[sup].mean()-tau[sup].mean())/tau[sup].mean()
    rows.append(r); print("seed %d done"%seed, file=sys.stderr)

t=pd.DataFrame(rows).set_index("seed")
print("\nBias (%) by estimator across 6 independent draws, n=50,000\n")
print(t.round(2).to_string())
print("\n" + "-"*78)
print(pd.DataFrame({"mean":t.mean(),"sd":t.std(),"min":t.min(),"max":t.max(),
                    "range":t.max()-t.min()}).round(2).to_string())
