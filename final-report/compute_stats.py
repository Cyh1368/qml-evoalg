#!/usr/bin/env python
"""Every statistic quoted in readme.md. Run: ../viz/.venv_render/bin/python compute_stats.py"""
import json,os,sys
sys.path.insert(0,'.')
import numpy as np
from scipy import stats as sps
from make_figures import ROWS, runs, wilson, boot_ci, ARMS

print("own+parsed proposals:", len(ROWS))
for setting in ("scratch","continue"):
    for arm in ARMS+(["frontier-no-gpt"] if setting=="continue" else []):
        rr=runs(setting,arm); g=[r for rs in rr.values() for r in rs]
        bests=[max(r["score"] for r in rs) for rs in rr.values()]
        m,lo,hi=boot_ci(bests)
        kd=sum("all-double" in r["circuit"]["labels"] for r in g)
        kt=sum("all-singular-tied" in r["circuit"]["labels"] for r in g)
        rd=sum(any("all-double" in r["circuit"]["labels"] for r in rs) for rs in rr.values())
        rt=sum(any("all-singular-tied" in r["circuit"]["labels"] for r in rs) for rs in rr.values())
        print(f"{setting:9s} {arm:17s} runs={len(rr):2d} props={len(g):3d} best={m:.3f}[{lo:.3f},{hi:.3f}] "
              f"K8 prop {kd}/{len(g)} run {rd}/{len(rr)} | tied prop {kt}/{len(g)} run {rt}/{len(rr)}")

print()
for arm in ARMS:
    rs=[r for r in ROWS if r["arm"]==arm and r["note"]]
    say=np.array([bool(r["note"]["build_claim"]) for r in rs])
    ident=np.array([bool(set(r["note"]["flags"])&{"names_perm","all_pairs","task_pairs"}) for r in rs])
    b=np.array([("all-double" in r["circuit"]["labels"]) for r in rs])
    a=int((say&b).sum()); bb=int((say&~b).sum()); c=int((~say&b).sum()); d=int((~say&~b).sum())
    n=len(rs); po=(a+d)/n; pe=((a+bb)*(a+c)+(c+d)*(bb+d))/n**2
    k=(po-pe)/(1-pe) if pe<1 else float('nan')
    p=sps.fisher_exact([[a,bb],[c,d]])[1]
    print(f"{arm:9s} n={n:3d} say&build={a} say&nobuild={bb} nosay&build={c} neither={d} kappa={k:.2f} fisher p={p:.2g}")
    print(f"          ident {ident.sum()}/{n}={ident.mean():.3f} say {say.sum()}/{n} build {b.sum()}/{n}"
          f"  P(build|say)={a/max(say.sum(),1):.2f} P(build|nosay)={c/max((~say).sum(),1):.2f} P(say|build)={a/max(b.sum(),1):.2f}")

# run-level fisher between arms
print()
def runsets(arm):
    rr={}
    for s in ("scratch","continue"): rr.update(runs(s,arm))
    return rr
for i in range(3):
    for j in range(i+1,3):
        A,B=ARMS[i],ARMS[j]
        out=[]
        for name,f in (("ident",lambda r: r["note"] and set(r["note"]["flags"])&{"names_perm","all_pairs","task_pairs"}),
                       ("claim",lambda r: r["note"] and r["note"]["build_claim"]),
                       ("build",lambda r: "all-double" in r["circuit"]["labels"])):
            ka=sum(any(f(r) for r in rs) for rs in runsets(A).values()); na=len(runsets(A))
            kb=sum(any(f(r) for r in rs) for rs in runsets(B).values()); nb=len(runsets(B))
            out.append(f"{name} {ka}/{na} vs {kb}/{nb} p={sps.fisher_exact([[ka,na-ka],[kb,nb-kb]])[1]:.3g}")
        print(A,"vs",B,"|"," | ".join(out))

# score by structure
print()
for name,f in (("none",lambda r: not ({"all-singular-tied","all-double"}&set(r["circuit"]["labels"]))),
               ("tied only",lambda r: "all-singular-tied" in r["circuit"]["labels"] and "all-double" not in r["circuit"]["labels"]),
               ("K8",lambda r: "all-double" in r["circuit"]["labels"])):
    xs=[r["score"] for r in ROWS if f(r)]; m,lo,hi=boot_ci(xs)
    print(f"{name:10s} n={len(xs):3d} mean={m:.3f} [{lo:.3f},{hi:.3f}] median={np.median(xs):.3f}")
a=[r["score"] for r in ROWS if "all-double" in r["circuit"]["labels"]]
b=[r["score"] for r in ROWS if "all-double" not in r["circuit"]["labels"]]
u,p=sps.mannwhitneyu(a,b); print("MW p",p, "cliffs", 2*u/(len(a)*len(b))-1)

# model attribution among frontier proposals
print()
import collections
cnt=collections.Counter()
for r in ROWS:
    if r["arm"] in ("frontier","frontier-no-gpt") and r["model"]:
        cnt[(r["model"].split("/")[-1], "all-double" in r["circuit"]["labels"])]+=1
mods=sorted({k[0] for k in cnt})
for m in mods:
    print(f"  {m:26s} {cnt[(m,True)]:3d} K8 / {cnt[(m,True)]+cnt[(m,False)]:3d} proposals")
