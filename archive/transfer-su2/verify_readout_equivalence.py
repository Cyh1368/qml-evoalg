#!/usr/bin/env python3
"""Check that the opaque-matrix readout reproduces the old Pauli-sum readout.

The v3 backend used to measure (XX + YY + ZZ)/3 written out in PennyLane Pauli
operators. That line stated the answer in a file the proposer can read, so it
was replaced by qml.Hermitian on a matrix loaded from the dataset. This must be
a pure refactor: identical expectation values, and gradients must still flow.
Also times both, since qml.Hermitian can be slower than a Pauli word and the
eval budget is real.

Run on the cluster with the qml-ea env active:
    python verify_readout_equivalence.py ~/project/zc_su2_v3/dataset.npz
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pennylane as qml
from pennylane import numpy as pnp

N_QUBITS = 8
N_REPEATS = 3

path = Path(sys.argv[1] if len(sys.argv) > 1 else "dataset.npz")
data = np.load(path)
PAIRS = [tuple(int(w) for w in row) for row in data["readout_pairs"]]
M = np.asarray(data["pair_observable"], dtype=complex)
STATES = np.asarray(data["x_validation"][:24], dtype=complex)

dev = qml.device("default.qubit", wires=N_QUBITS, shots=None)


def ansatz(params):
    """A deliberately generic, non-equivariant block; exercises every gate path."""
    for _ in range(N_REPEATS):
        for w in range(N_QUBITS):
            qml.RY(params[0], wires=w)
        for a, b in [(0, 1), (2, 3), (4, 5), (6, 7)]:
            qml.IsingXX(params[1], wires=[a, b])
            qml.IsingZZ(params[2], wires=[a, b])
        for w in range(N_QUBITS - 1):
            qml.CZ(wires=[w, w + 1])


@qml.qnode(dev, interface="autograd", diff_method="backprop")
def old_readout(states, params):
    qml.StatePrep(states, wires=range(N_QUBITS))
    ansatz(params)
    return [
        qml.expval((qml.PauliX(a) @ qml.PauliX(b)
                    + qml.PauliY(a) @ qml.PauliY(b)
                    + qml.PauliZ(a) @ qml.PauliZ(b)) / 3.0)
        for a, b in PAIRS
    ]


@qml.qnode(dev, interface="autograd", diff_method="backprop")
def new_readout(states, params):
    qml.StatePrep(states, wires=range(N_QUBITS))
    ansatz(params)
    return [qml.expval(qml.Hermitian(M, wires=[a, b])) for a, b in PAIRS]


rng = np.random.default_rng(0)
worst = 0.0
for trial in range(5):
    p = pnp.array(rng.uniform(-np.pi, np.pi, size=3), requires_grad=True)
    a = np.asarray(old_readout(STATES, p), dtype=float)
    b = np.asarray(new_readout(STATES, p), dtype=float)
    worst = max(worst, float(np.max(np.abs(a - b))))
print(f"max |old - new| over 5 random parameter draws, {len(PAIRS)} pairs x "
      f"{len(STATES)} states: {worst:.3e}")
assert worst < 1e-10, "readouts disagree -- NOT a pure refactor"


def scalar(fn, params):
    return pnp.mean(pnp.stack(fn(STATES, params)))


p = pnp.array(rng.uniform(-np.pi, np.pi, size=3), requires_grad=True)
g_old = qml.grad(lambda q: scalar(old_readout, q))(p)
g_new = qml.grad(lambda q: scalar(new_readout, q))(p)
print(f"gradient old: {np.array2string(np.asarray(g_old), precision=6)}")
print(f"gradient new: {np.array2string(np.asarray(g_new), precision=6)}")
assert np.allclose(g_old, g_new, atol=1e-10), "gradients disagree"

for name, fn in [("pauli-sum", old_readout), ("hermitian", new_readout)]:
    fn(STATES, p)  # warm up
    t0 = time.perf_counter()
    for _ in range(5):
        qml.grad(lambda q: scalar(fn, q))(p)
    print(f"{name:10s} {(time.perf_counter() - t0) / 5:.4f} s per forward+backward")

print("PASS: opaque readout is numerically identical and differentiable")
