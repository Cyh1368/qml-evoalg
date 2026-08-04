#!/usr/bin/env python3
"""Add the readout observable to dataset.npz as an opaque numeric matrix.

Motivation: the fixed readout used to be written out in the backend as
(XX + YY + ZZ)/3 in PennyLane Pauli operators. In the contextualized arm the
seed file is shown to the proposer in full, so that line stated the answer the
search is meant to discover; in the zero-context arm it was reachable because
the evolve block is arbitrary Python and can import the backend. Shipping the
same operator as an unlabelled 4x4 matrix in the dataset removes the plain-text
statement from every file the proposer can read, while leaving the numerics
exactly unchanged.

Existing arrays are copied through untouched, so states, labels, groups and
pairs stay bit-identical to the shipped v3 dataset.

Run: python add_pair_observable.py path/to/dataset.npz
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)


def pair_observable() -> np.ndarray:
    """(X@X + Y@Y + Z@Z)/3 on two qubits; equals (2*SWAP - I)/3."""
    m = (np.kron(X, X) + np.kron(Y, Y) + np.kron(Z, Z)) / 3.0
    swap = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=complex)
    assert np.allclose(m, (2 * swap - np.eye(4)) / 3.0)
    assert np.allclose(m, m.conj().T), "observable must be Hermitian"
    # Symmetric under exchanging the two wires, so wire order cannot matter.
    perm = swap @ m @ swap
    assert np.allclose(m, perm), "observable must be wire-order independent"
    return m


def main(path: Path) -> int:
    data = np.load(path)
    arrays = {k: data[k] for k in data.files}
    if "pair_observable" in arrays:
        print(f"{path.name}: pair_observable already present; leaving unchanged")
        return 0
    arrays["pair_observable"] = pair_observable()
    np.savez_compressed(path, **arrays)

    check = np.load(path)
    for k in data.files:
        assert np.array_equal(check[k], data[k]), f"array {k} changed"
    print(f"{path}: added pair_observable {check['pair_observable'].shape}; "
          f"{len(data.files)} pre-existing arrays verified unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1])))
