"""Shared dense-simulation helpers. Single source of truth.

Duplicate copies of shared structures rot: in the previous project a locally copied panel silently
drifted from the canonical one and changed a reported number. Everything that needs a Pauli string,
a matrix exponential or a Neel state imports it from here.
"""

from __future__ import annotations

import numpy as np


def pauli_chain(n, site, op):
    """Single-site Pauli on `site` of an n-qubit register, as a dense 2^n x 2^n matrix."""
    p = {"I": np.eye(2, dtype=complex), "X": np.array([[0, 1], [1, 0]], dtype=complex),
         "Y": np.array([[0, -1j], [1j, 0]], dtype=complex),
         "Z": np.array([[1, 0], [0, -1]], dtype=complex)}[op]
    out = np.array([[1.0 + 0j]])
    for i in range(n):
        out = np.kron(out, p if i == site else np.eye(2, dtype=complex))
    return out


def two_site(n, i, j, op):
    a = pauli_chain(n, i, op)
    b = pauli_chain(n, j, op)
    return a @ b


def heisenberg_hamiltonian(n, J_alt, lam):
    """Bond-alternating Heisenberg chain plus a staggered field.

    H = sum_b J_b (XX + YY + ZZ) + lam * sum_i (-1)^i Z_i, open boundaries. J alternates so the
    chain has a two-site unit cell; lam breaks the site-exchange symmetry that the readout error
    also breaks, which is what makes the symmetry *approximately* available.
    """
    dim = 2 ** n
    H = np.zeros((dim, dim), dtype=complex)
    for b in range(n - 1):
        J = J_alt if b % 2 == 0 else 1.0
        for op in ("X", "Y", "Z"):
            H += J * two_site(n, b, b + 1, op)
    for i in range(n):
        H += lam * ((-1) ** i) * pauli_chain(n, i, "Z")
    return H


def neel_state(n):
    """|up down up down ...> as a state vector (site 0 is the most significant bit)."""
    psi = np.zeros(2 ** n, dtype=complex)
    bits = 0
    for i in range(n):
        if i % 2 == 0:                       # spin up = |0>, so bit 0
            pass
        else:
            bits |= 1 << (n - 1 - i)
    psi[bits] = 1.0
    return psi


def amplitude_damp(rho, n, gamma, sites=None):
    """Amplitude damping channel applied on the given sites (default all)."""
    sites = range(n) if sites is None else sites
    for i in sites:
        kp = np.sqrt(gamma) * pauli_chain(n, i, "Z") @ pauli_chain(n, i, "|0><1|")
        k0 = np.eye(2 ** n, dtype=complex) - 0.5 * (kp.conj().T @ kp)
        rho = k0 @ rho @ k0.conj().T + kp @ rho @ kp.conj().T
    return rho


def expm_hermitian(A):
    """exp(A) for Hermitian A. Do NOT feed this an anti-Hermitian matrix: hermitising -i*t*H
    gives 0 and exp(0) = I, which is a silent "nothing evolves" bug that produced an entire
    degenerate task before the response was checked against t=0."""
    w, V = np.linalg.eigh(0.5 * (A + A.conj().T))
    return (V * np.exp(w)) @ V.conj().T


def eig_hermitian(A, tol=1e-9):
    """Eigendecomposition of a Hermitian matrix, for reuse across evolution times.

    The symmetrisation that makes this convenient also *hides* a non-Hermitian Hamiltonian: a
    mis-commuted term (X and Z on the same site) was fed through here, came out Hermitian, and the
    task reported a constant response with no error anywhere. So the Hermiticity is asserted, with
    a tolerance, rather than assumed.
    """
    if np.max(np.abs(A - A.conj().T)) > tol * max(1.0, np.max(np.abs(A))):
        raise ValueError("Hamiltonian is not Hermitian: max|H - H^dag| = %.3e"
                         % float(np.max(np.abs(A - A.conj().T))))
    return np.linalg.eigh(0.5 * (A + A.conj().T))


def unitary_from_eig(w, V, t):
    """exp(-i t H) from a cached eigendecomposition H = V diag(w) V^H."""
    return (V * np.exp(-1j * float(t) * w)) @ V.conj().T
