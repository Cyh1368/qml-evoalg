import itertools, json
import numpy as np
from symmetry import unitary, defects, adjacent_swaps

def run():
    n=3; perms=list(itertools.permutations(range(n)))
    all_cz=[{'gate':'CZ','wires':[i,j]} for i in range(n) for j in range(i+1,n)]
    collective=[{'gate':'RY','wire':i,'param':'a'} for i in range(n)]
    ordered=[{'gate':'CRX','wires':[i,j],'param':'a'} for i in range(n) for j in range(n) if i!=j]
    commuting=[dict(g,gate='CRZ') for g in ordered]
    results={}
    for label,g in [('all_cz',all_cz),('collective',collective),('ordered_all_crx',ordered),('all_crz',commuting)]:
        u=unitary(g,{'a':0.7},n)
        assert np.allclose(u.conj().T@u,np.eye(2**n))
        results[label]=defects(u,perms)
    assert results['all_cz']['channel_max']<1e-12
    assert results['collective']['channel_max']<1e-12
    assert results['all_crz']['channel_max']<1e-12
    assert results['ordered_all_crx']['channel_max']>0.001
    # Z anticommutes with X: strict commutation differs from channel covariance.
    z=np.diag([1.,-1.]); x=np.array([[0.,1.],[1.,0.]])
    assert np.isclose(np.linalg.norm(z-x@z@x)**2/4, 2)
    assert 1-abs(np.vdot(z,x@z@x)/2)**2 == 0
    # Group twirl identity, with explicit full group enumeration.
    u=unitary(ordered,{'a':0.7},n)
    from symmetry import permutation_indices
    twirl=sum(u[np.ix_(permutation_indices(p),permutation_indices(p))] for p in perms)/len(perms)
    assert np.allclose(np.linalg.norm(u-twirl)**2/len(u),results['ordered_all_crx']['unitary_mean'])
    print(json.dumps(results,indent=2))
if __name__=='__main__': run()
