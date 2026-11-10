import json
from pathlib import Path
import numpy as np
from symmetry import unitary, defects, adjacent_swaps
root=Path(__file__).resolve().parents[2]
text=(root/'viz/circuits/circuits_data.js').read_text()
circuits=json.loads(text.split('=',1)[1].strip().rstrip(';'))
rng=np.random.default_rng(20261110)
rows=[]
for c in circuits:
    keys=sorted({g['param'] for g in c['gates'] if g.get('param') is not None})
    draws=[]
    for _ in range(3):
        params=dict(zip(keys,rng.uniform(-np.pi,np.pi,len(keys))))
        draws.append(defects(unitary(c['gates'],params,8),adjacent_swaps(8)))
    rows.append({'key':c['key'],'source':c.get('source'),'draws':draws})
# Same gate count and parameter names throughout; controlled loss of tying.
gates=[{'gate':'RY','wire':i,'param':str(i)} for i in range(4)]
direction=np.array([-1.5,-0.5,0.5,1.5]); sweep=[]
for eps in [0.,0.01,0.03,0.1,0.3,1.]:
    params=dict(zip(map(str,range(4)),0.7+eps*direction))
    sweep.append({'epsilon':eps,**defects(unitary(gates,params,4),adjacent_swaps(4))})
out={'seed':20261110,'scope':'untrained ansatz block, adjacent transposition residuals; no performance claims','gallery':rows,'controlled_untying':sweep,'repair':'Project rotation angles to their mean; equals epsilon=0 for every sweep row.'}
(root/'research/metrics/pilot.json').write_text(json.dumps(out,indent=2))
print('Analyzed',len(rows),'gallery circuits and',len(sweep),'controlled interventions')
