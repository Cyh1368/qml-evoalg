"""Matched-budget random-search training on disjoint S3 orbits; development only."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import itertools,json
from pathlib import Path
import numpy as np
from symmetry import unitary
root=Path(__file__).resolve().parent
n=3; d=8
angles=[.15,.55,1.05,1.65,2.3]
# Allocate whole unordered triples, before constructing any observations.
orbits=list(itertools.combinations_with_replacement(angles,n))
split_rng=np.random.default_rng(789)
order=split_rng.permutation(len(orbits)); train_ids=set(map(int,order[:20])); dev_ids=set(map(int,order[20:30]))
# Last 5 held-out orbit IDs remain unevaluated. No target/state generation for them.
def states_for(ids):
    xs=[x for i,o in enumerate(orbits) if i in ids for x in sorted(set(itertools.permutations(o)))]
    states=[]
    for x in xs:
        s=np.array([1.])
        for a in x:s=np.kron(s,[np.cos(a/2),np.sin(a/2)])
        states.append(s)
    return np.array(xs),np.array(states)
xtrain,strain=states_for(train_ids); xdev,sdev=states_for(dev_ids)
zmean=np.array([np.mean([1-2*((i>>(2-j))&1) for j in range(3)]) for i in range(8)])
rot=[{'gate':'RY','wire':i,'param':'a'} for i in range(3)]
def predict(params,mode,states):
    a,b,c=params
    if mode=='sham': a+=.3  # shared-angle intervention; directed CRZ retained
    gates=list(rot)
    for i in range(3):
        for j in range(i+1,3):
            gates.append({'gate':'CRZ','wires':[i,j],'param':'b'})
            if mode=='repaired':gates.append({'gate':'CRZ','wires':[j,i],'param':'b'})
    gates += [{'gate':'RY','wire':i,'param':'c'} for i in range(3)]
    u=unitary(gates,{'a':a,'b':b/2 if mode=='repaired' else b,'c':c},3)
    return abs(states@u.T)**2@zmean
true=np.array([.38,.83,-.61])
def targets(states,eta):
    sym=predict(true,'repaired',states)
    broken=predict(true,'original',states)
    return (1-eta)*sym+eta*broken
rows=[]; budget=128
for eta in [0.,.5,1.]:
    yt=targets(strain,eta); yd=targets(sdev,eta)
    for seed in range(8):
        rng=np.random.default_rng(seed)
        proposals=rng.uniform(-np.pi,np.pi,(budget,3))
        for mode in ['original','repaired','sham']:
            losses=[]
            for p in proposals:losses.append(float(np.mean((predict(p,mode,strain)-yt)**2)))
            best=int(np.argmin(losses)); chosen=proposals[best]
            pred=predict(chosen,mode,sdev)
            rows.append(dict(eta=eta,seed=seed,mode=mode,budget=budget,selected_index=best,parameters=chosen.tolist(),train_mse=losses[best],dev_mse=float(np.mean((pred-yd)**2))))
summary=[]
for eta in [0.,.5,1.]:
    for mode in ['repaired','sham']:
        differences=[]
        for seed in range(8):
            old=next(r for r in rows if r['eta']==eta and r['seed']==seed and r['mode']=='original')
            new=next(r for r in rows if r['eta']==eta and r['seed']==seed and r['mode']==mode)
            differences.append(old['dev_mse']-new['dev_mse'])
        summary.append(dict(eta=eta,comparison='original minus '+mode,mean_difference=float(np.mean(differences)),improved_seeds=sum(v>0 for v in differences),paired_differences=differences))
out={'scope':'development pilot only; no test states or labels generated/evaluated','optimizer':'paired uniform parameter search; select minimum training MSE only','budget_per_arm':budget,'train_orbits':sorted(train_ids),'dev_orbits':sorted(dev_ids),'sealed_test_orbits':sorted(set(range(len(orbits)))-train_ids-dev_ids),'train_samples':len(strain),'dev_samples':len(sdev),'gate_counts':{'original':9,'repaired':12,'sham':9},'parameters_per_arm':3,'sham':'shared first RY angle shifted by .3, retaining directed CRZ; search distribution control, not a pure causal control','rows':rows,'summary':summary}
(root/'training_pilot.json').write_text(json.dumps(out,indent=2))
print(json.dumps(summary,indent=2))
