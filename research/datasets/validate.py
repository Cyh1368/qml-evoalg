"""Validate generated files, exact labels, orbit separation and ring target law."""
import hashlib
import json
from itertools import combinations
from pathlib import Path
import numpy as np
from generate import ring_canonical
HERE=Path(__file__).resolve().parent
manifest=json.loads((HERE/'manifest.json').read_text())
report={}
for name,meta in manifest['families'].items():
    for file,sha in meta['files'].items():assert hashlib.sha256((HERE/file).read_bytes()).hexdigest()==sha
    dev=np.load(HERE/'development'/f'{name}.npz'); test=np.load(HERE/'locked_holdout'/f'{name}.npz')
    assert not any('test' in key for key in dev.files)
    sets={s:set((test if s=='test' else dev)['orbit_'+s].tolist()) for s in ['train','validation','test']}
    for a,b in combinations(sets,2):assert sets[a].isdisjoint(sets[b])
    if name.startswith('graphs'):
        assert sum(map(len,sets.values()))==156
        pairs=[tuple(p) for p in meta['feature_pairs']]; index={p:i for i,p in enumerate(pairs)}
        orbit_by_graph={}; label_by_graph={}
        for split in sets:
            data=test if split=='test' else dev
            for row,orbit,label,triangle in zip(data['x_'+split],data['orbit_'+split],data['y_connected_'+split],data['y_triangle_'+split]):
                adjacency=[set() for _ in range(6)]
                for bit,(a,b) in zip(row,pairs):
                    if bit:adjacency[a].add(b);adjacency[b].add(a)
                seen={0}; stack=[0]
                while stack:
                    for b in adjacency[stack.pop()]-seen:seen.add(b);stack.append(b)
                assert (label==1)==(len(seen)==6)
                assert (triangle==1)==any(b in adjacency[a] and c in adjacency[a] and c in adjacency[b] for a,b,c in combinations(range(6),3))
                key=sum(int(bit)<<k for k,bit in enumerate(row)); orbit_by_graph[key]=int(orbit)
        assert len(orbit_by_graph)==32768
        # Adjacent transpositions generate S6: canonical ID constant on each generator edge.
        for key,canonical in orbit_by_graph.items():
            for j in range(5):
                perm=list(range(6));perm[j],perm[j+1]=perm[j+1],perm[j]
                transformed=sum(((key>>k)&1)<<index[tuple(sorted((perm[a],perm[b])))] for k,(a,b) in enumerate(pairs))
                assert orbit_by_graph[transformed]==canonical
        report[name]='PASS: 32768 labels independently checked; 156 disjoint orbits; all S6 generator edges checked'
    else:
        x=dev['x_train']; canonical=ring_canonical(x)
        inv=lambda v:np.mean(v*np.roll(v,1,axis=1),axis=1)
        base=inv(x); d1=[]
        for reflected in [x,x[:,::-1]]:
            for k in range(6):
                transformed=np.roll(reflected,k,axis=1)
                assert np.array_equal(ring_canonical(transformed),canonical)
                assert np.allclose(inv(transformed),base)
                delta=(transformed[:,0]-transformed.mean(axis=1))-(x[:,0]-x.mean(axis=1))
                d1.append(delta**2)
                for a in meta['alphas']:
                    actual=inv(transformed)+a*(transformed[:,0]-transformed.mean(axis=1))-dev[f'y_alpha_{a:g}_train']
                    assert np.allclose(actual**2,a*a*delta**2,atol=1e-14)
        report[name]={'status':'PASS: all D6 transforms preserve canonical IDs and alpha-squared defect law','train_breaking_component_defect':float(np.mean(d1))}
(HERE/'validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
