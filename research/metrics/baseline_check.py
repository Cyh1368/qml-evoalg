import ast,json
from pathlib import Path
from symmetry import unitary, defects, adjacent_swaps
root=Path(__file__).resolve().parents[2]
tree=ast.parse((root/'experiments/transfer-sn/baseline_program.py').read_text())
gates=next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ANSATZ_SPEC' for t in node.targets))
params={'ry_all':0.31,'rz_all':-0.23,'crz_all':0.7}
repaired=[]
for g in gates:
    if g['gate']=='CRZ':
        repaired += [dict(g,param='half'),dict(g,wires=g['wires'][::-1],param='half')]
    else: repaired.append(g)
params['half']=params['crz_all']/2
out={k:defects(unitary(gs,params,8),adjacent_swaps(8)) for k,gs in [('original',gates),('bidirectional_half_angle',repaired)]}
assert out['original']['channel_mean']>0.01
assert out['bidirectional_half_angle']['channel_max']<1e-12
(root/'research/metrics/baseline_check.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
