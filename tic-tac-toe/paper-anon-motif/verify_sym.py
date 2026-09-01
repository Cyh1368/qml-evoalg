"""What symmetry does each dataset actually have? Establish ground truth
before judging whether the search found it."""
import itertools
import numpy as np

# ---------------------------------------------------------------- S_n task
z = np.load("/home/ch2499/project/transfer_sn/dataset.npz", allow_pickle=True)
pairs = z["feature_pairs"].astype(int)
X = np.concatenate([z["x_train"], z["x_validation"], z["x_test"]])
Y = np.concatenate([z["y_train"], z["y_validation"], z["y_test"]])
print("=" * 66)
print("transfer_sn: %d records, %d features, pair table covers %d of C(8,2)=28"
      % (len(X), X.shape[1], len(set(map(tuple, np.sort(pairs, 1))))))
print("labels:", dict(zip(*np.unique(Y, return_counts=True))))


def to_adj(x):
    A = np.zeros((8, 8), int)
    for v, (i, j) in zip(x, pairs):
        A[i, j] = A[j, i] = int(v > 0)
    return A


def invariants(A):
    deg = tuple(sorted(A.sum(1)))
    tri = int(np.trace(np.linalg.matrix_power(A, 3)) // 6)
    ev = tuple(np.round(np.sort(np.linalg.eigvalsh(A)), 6))
    return deg, A.sum() // 2, tri, ev


# does a permutation-invariant description determine the label?
buckets = {}
for x, y in zip(X, Y):
    buckets.setdefault(invariants(to_adj(x)), []).append(y)
pure = sum(1 for v in buckets.values() if len(set(v)) == 1)
covered = sum(len(v) for v in buckets.values() if len(set(v)) == 1)
print("distinct isomorphism-invariant classes: %d" % len(buckets))
print("classes with a single label: %d/%d  (covering %d/%d records = %.1f%%)"
      % (pure, len(buckets), covered, len(X), 100 * covered / len(X)))

# direct test: relabel nodes, does the label survive?
rng = np.random.default_rng(0)
idx = {tuple(np.sort(p)): k for k, p in enumerate(pairs)}
same = tot = 0
lookup = {tuple(x): y for x, y in zip(X, Y)}
for _ in range(4000):
    k = rng.integers(len(X))
    perm = rng.permutation(8)
    A = to_adj(X[k])
    B = A[np.ix_(perm, perm)]
    xb = np.array([B[i, j] for i, j in pairs], dtype=np.int8)
    hit = lookup.get(tuple(xb))
    if hit is not None:
        tot += 1
        same += (hit == Y[k])
print("permuted copies found in dataset: %d, label preserved in %d (%.0f%%)"
      % (tot, same, 100 * same / max(tot, 1)))

# ------------------------------------------------------------- SU(2) task
z2 = np.load("/home/ch2499/project/transfer_su2/dataset.npz", allow_pickle=True)
S = np.concatenate([z2["x_train"], z2["x_validation"], z2["x_test"]])
Y2 = np.concatenate([z2["y_train"], z2["y_validation"], z2["y_test"]])
print("=" * 66)
print("transfer_su2: %d states, dim %d" % (len(S), S.shape[1]))
print("labels:", dict(zip(*np.unique(Y2, return_counts=True))))

sx = np.array([[0, 1], [1, 0]], complex)
sy = np.array([[0, -1j], [1j, 0]])
sz = np.array([[1, 0], [0, -1]], complex)


def op_on(op, k, n=8):
    m = np.array([[1]], complex)
    for q in range(n):
        m = np.kron(m, op if q == k else np.eye(2))
    return m


Sx = sum(op_on(sx, k) for k in range(8)) / 2
Sy = sum(op_on(sy, k) for k in range(8)) / 2
Sz = sum(op_on(sz, k) for k in range(8)) / 2
S2 = Sx @ Sx + Sy @ Sy + Sz @ Sz

vals = np.array([np.real(np.vdot(v, S2 @ v)) for v in S[:400]])
lab = Y2[:400]
print("<S^2> by label:")
for L in np.unique(lab):
    v = vals[lab == L]
    print("   label %+.0f : mean %.3f  min %.3f  max %.3f" % (L, v.mean(), v.min(), v.max()))
# separability
thr = (vals[lab > 0].mean() + vals[lab < 0].mean()) / 2
acc = max((vals > thr) == (lab > 0), (vals < thr) == (lab > 0), key=lambda m: m.mean()).mean()
print("thresholding <S^2> alone classifies %.1f%% of states" % (100 * acc))
