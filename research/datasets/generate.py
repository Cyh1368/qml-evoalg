"""Deterministic small benchmarks. Run python3 research/datasets/generate.py.

Holdout files are an access contract, not a filesystem security boundary.
Never pass locked_holdout/ to search. Graph canonicalization is exhaustive.
"""
from pathlib import Path
from itertools import combinations, permutations
import hashlib
import json
import numpy as np

HERE=Path(__file__).resolve().parent
SEED=20261110

def canonical_graph_ids(n):
    pairs=list(combinations(range(n),2)); index={p:i for i,p in enumerate(pairs)}
    ids=np.arange(1<<len(pairs),dtype=np.uint32)
    bits=((ids[:,None] >> np.arange(len(pairs)))&1).astype(np.uint8)
    canonical=ids.copy()
    for perm in permutations(range(n)):
        transformed=np.zeros(len(ids),dtype=np.uint32)
        for j,(a,b) in enumerate(pairs):
            k=index[tuple(sorted((perm[a],perm[b])))]; transformed |= bits[:,j].astype(np.uint32)<<k
        np.minimum(canonical,transformed,out=canonical)
    return pairs,bits,canonical

def graph_labels(bits,pairs,n):
    adj=np.zeros((len(bits),n,n),dtype=bool)
    for k,(a,b) in enumerate(pairs): adj[:,a,b]=adj[:,b,a]=bits[:,k]
    reach=adj.copy()
    for k in range(n): reach |= reach[:,:,k,None] & reach[:,None,k,:]
    connected=reach.all(axis=(1,2))
    triangle=np.zeros(len(bits),dtype=bool)
    for a,b,c in combinations(range(n),3): triangle |= adj[:,a,b]&adj[:,b,c]&adj[:,a,c]
    return {'connected':connected.astype(np.int8)*2-1,'triangle':triangle.astype(np.int8)*2-1}

def split_orbits(ids,rng):
    unique=np.unique(ids); rng.shuffle(unique)
    a=int(.6*len(unique)); b=int(.8*len(unique))
    return {name:np.isin(ids,group) for name,group in zip(('train','validation','test'),(unique[:a],unique[a:b],unique[b:]))}

def ring_canonical(x):
    return np.array([min(tuple(np.roll(v,k)) for v in (row,row[::-1]) for k in range(len(row))) for row in x])

def save_family(name,x,ys,orbit,split,metadata):
    development=HERE/'development'; locked=HERE/'locked_holdout'
    development.mkdir(exist_ok=True); locked.mkdir(exist_ok=True)
    payload={}; test={}; counts={}
    for s,mask in split.items():
        dest=test if s=='test' else payload
        dest['x_'+s]=x[mask]; dest['orbit_'+s]=orbit[mask]
        for task,y in ys.items():dest['y_'+task+'_'+s]=y[mask]
        counts[s]={'rows':int(mask.sum()),'orbits':int(len(np.unique(orbit[mask]))),'target_means':{task:float(y[mask].mean()) for task,y in ys.items()}}
    paths=[development/(name+'.npz'),locked/(name+'.npz')]
    np.savez_compressed(paths[0],**payload); np.savez_compressed(paths[1],**test)
    return dict(metadata,counts=counts,files={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})

def main():
    rng=np.random.default_rng(SEED); n=6
    pairs,x,orbit=canonical_graph_ids(n); ys=graph_labels(x,pairs,n)
    graph=save_family('graphs_n6',x,ys,orbit,split_orbits(orbit,rng),{'n':n,'feature_pairs':pairs,'group':'S6','sampling':'All 32768 labeled simple graphs, split by shuffled exact isomorphism classes; uniform labeled-graph weights within each split. No class balancing.','tasks':['connected','triangle']})
    x=rng.uniform(-1,1,size=(1200,6)); canon=ring_canonical(x)
    _,orbit=np.unique(canon,axis=0,return_inverse=True)
    invariant=np.mean(x*np.roll(x,1,axis=1),axis=1)
    breaking=x[:,0]-x.mean(axis=1)
    alphas=[0.,.1,.25,.5,1.]
    ys={f'alpha_{a:g}':invariant+a*breaking for a in alphas}
    ring=save_family('ring_n6',x,ys,orbit,split_orbits(orbit,rng),{'n':6,'group':'D6','sampling':'1200 independent Uniform([-1,1]^6) vectors; exact dihedral orbit split','alphas':alphas,'target':'mean_i x_i*x_(i+1) + alpha*(x_0-mean_i x_i)','note':'Alpha=0 invariant; positive alpha intentionally breaks D6. Target group-averaged squared defect is alpha^2 times the breaking-component defect. These are different targets on identical inputs, not independent tasks.'})
    manifest={'seed':SEED,'protocol':'Fresh prospective benchmark; generated after retrospective audit. Keep locked_holdout outside search context. Split and targets fixed before training.','families':{'graphs_n6':graph,'ring_n6':ring}}
    (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v['counts'] for k,v in manifest['families'].items()},indent=2))
if __name__=='__main__':main()
