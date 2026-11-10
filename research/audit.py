"""Reproduce dataset audit and prospective evaluator leakage regression.
Run: python3 research/audit.py. Requires numpy only; never executes candidates.
"""
import ast
import json
import math
import os
import tempfile
from collections import Counter
from itertools import combinations
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]

def main():
    data = np.load(ROOT / 'experiments/transfer-sn/dataset.npz')
    names = ['train', 'validation', 'test']
    report = {'split_sizes': {}, 'exact_overlap': {}, 'edge_threshold_baseline': {}}
    sets = {}
    for name in names:
        x, y = data['x_'+name], data['y_'+name]
        report['split_sizes'][name] = {'n': len(y), 'positive': int((y>0).sum()), 'unique':len({r.tobytes() for r in x})}
        sets[name] = {r.tobytes() for r in x}
    for a,b in combinations(names,2):
        report['exact_overlap'][a+'_'+b] = len(sets[a]&sets[b])
    # Fit only on training; smallest maximizing threshold fixes ties in advance.
    train_edges=data['x_train'].sum(axis=1)
    acc=[float(np.mean((train_edges>=t)==(data['y_train']>0))) for t in range(30)]
    threshold=int(np.argmax(acc))
    report['edge_threshold_baseline']['threshold']=threshold
    for name in names:
        report['edge_threshold_baseline'][name]=float(np.mean((data['x_'+name].sum(axis=1)>=threshold)==(data['y_'+name]>0)))
    rows=json.loads((ROOT/'analysis/report/data/labels.json').read_text())
    selected=[r for r in rows if r.get('own') and r.get('parsed') and not(r['setting']=='scratch' and r['generation']>20)]
    report['report_rows']={'raw':len(rows),'selected':len(selected),'arms':dict(Counter(r['arm'] for r in selected))}
    # Load only actual evaluator function definitions, avoiding optional shinka import.
    tree=ast.parse((ROOT/'experiments/transfer-sn/evaluate.py').read_text())
    funcs=ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) or (isinstance(n,ast.ImportFrom) and n.module=='__future__')],type_ignores=[])
    env=dict(np=np,math=math,Path=Path,json=json,USE_TEST_IN_SCORE=False,N_EPOCHS=1000,STEPS_PER_EPOCH=30,SEED_TOTAL_PARAMS=146,SCORE_RESCALE=False)
    exec(compile(funcs,'evaluate.py','exec'),env)
    base=dict(train_accuracy=.9,validation_accuracy=.8,validation_loss=.3,n_params=20,max_steps=30000,convergence_step=100,depth=10,gate_count=20)
    a=dict(base,test_accuracy=.1,test_loss=3.,generalization_gap=.8,parameter_efficiency=.005)
    b=dict(base,test_accuracy=.99,test_loss=.01,generalization_gap=.09,parameter_efficiency=.0495)
    assert env['score_result'](a)==env['score_result'](b)
    with tempfile.TemporaryDirectory() as d:
        aa=env['aggregate_metrics']([a],d); bb=env['aggregate_metrics']([b],d)
        assert aa['public']==bb['public'] and aa['text_feedback']==bb['text_feedback']
        assert not any(k.startswith('test_') for k in aa['public'])
    report['prospective_regression']='PASS: default score, public metrics and feedback invariant to test-derived fields'
    out=ROOT/'research/audit_results.json'; out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()
