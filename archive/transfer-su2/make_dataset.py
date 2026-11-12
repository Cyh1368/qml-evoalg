"""Offline dataset generator for transfer task B (run locally, NEVER shipped
to the evolution loop). Produces dataset.npz of precomputed 8-qubit state
vectors + binary labels, consumed opaquely by initial_program.py — no
Hamiltonian, model name, or labeling rule appears in any code the LLM sees.

Task (known only to us): low-energy states of the bond-alternating spin-1/2
Heisenberg XXX ring, H = sum_i J_i (X_i X_{i+1} + Y_i Y_{i+1} + Z_i Z_{i+1}),
J alternating (1, j) around an 8-site PERIODIC ring. Label = which bond
sublattice is strong: j < 1 (-1) vs j > 1 (+1) — the two dimerized phases.

Why periodic: a one-site translation maps the j phase into the 1/j phase, and
the fixed uniform readout (mean over ring bonds) is translation-invariant, so
a circuit must break the even/odd symmetry to separate the classes at all.

Ground-truth structure (the answer key, absent from shipped artifacts):
  * global SU(2) spin-rotation symmetry -> equivariant gates are isotropic
    exchange interactions, i.e. tied RXX=RYY=RZZ angles on a pair;
  * bond-alternation -> even/odd bond structure (broken translation, period 2).

Qubit labels are scrambled by a fixed permutation so that "neighboring" sites
are not adjacent integer wires (removes the chain-geometry hint).

--------------------------------------------------------------------------
v3 (2026-07-29): make the SU(2) symmetry PAY, without saying that it exists.

v1 and v2 both failed for the same reason: an SU(2)-equivariant circuit had no
measurable advantage over a generic one, so the fitness ranked by parameter
count and the search reduced to an economy climb (v2 postmortem:
context/zc-su2-v2-results-2026-07-29.md, Spearman(names, score) = -0.984).

Two changes, both in the DATA and the readout — neither in the scorer, which
still measures only accuracy, margin, parameter count, gap and convergence:

  1. MAGNETIZATION_SECTOR = 1. v1/v2 used the true ground state, which for an
     even bipartite antiferromagnetic ring is a total-spin SINGLET and is
     therefore itself invariant under global spin rotation. Every correlator
     component was equal (<XX> = <YY> = <ZZ> on every pair), so the frame
     carried no information and equivariance bought nothing. The lowest state
     in the total-S_z = +1 block is an S=1 multiplet member: global rotations
     act on it non-trivially, while every S_i . S_j expectation is unchanged.

  2. Each sample gets its own Haar-random global rotation r^{(x)8}. The label
     is untouched by construction (it is a property of the Hamiltonian), and
     the invariant bond correlators are untouched (they commute with the
     rotation), but the single-component correlators are scrambled.

Consequence, which is what the fitness can now see: a circuit U whose
conjugated readout U^dag M U is SU(2)-invariant has an EXACTLY frame-
independent decision function and generalises from a handful of training
samples; any other circuit sees a different frame on every held-out sample.
The readout M is made invariant to match (see initial_program.py). Nothing
about rotations, invariance or the Hamiltonian is stated anywhere the
proposer can read: it observes only that some circuits generalise and others
do not.

Honest limit of the claim: this makes the symmetry USEFUL, which is a
precondition for discovering it by search. It does not tell the model the
symmetry is there. Those are different things and the writeup must say so.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
N = 8
DIM = 2 ** N
RNG = np.random.default_rng(2027)

QUBIT_RELABEL = RNG.permutation(N)  # site s -> qubit QUBIT_RELABEL[s]

X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
I2 = np.eye(2, dtype=complex)


def two_site(op: np.ndarray, a: int, b: int) -> np.ndarray:
    mats = [I2] * N
    mats[a] = op
    mats[b] = op
    out = mats[0]
    for m in mats[1:]:
        out = np.kron(out, m)
    return out


# Precompute bond operators on SITE indices (0..7 around the ring).
BONDS = [(s, (s + 1) % N) for s in range(N)]
BOND_OPS = [
    two_site(X, a, b) + two_site(Y, a, b) + two_site(Z, a, b)
    for a, b in BONDS
]


DISORDER = 0.35  # per-bond multiplicative coupling disorder, U[1-d, 1+d]
GAP_MIN = 0.05   # reject samples whose realized sublattice gap is ambiguous

# v3: work one magnon above the singlet so that global spin rotations act
# non-trivially on the state. The true ground state (sector 0) is an S=0
# singlet and is its own orbit under SU(2) — that is what made v1/v2 blind.
MAGNETIZATION_SECTOR = 1


def _one_site(op: np.ndarray, a: int) -> np.ndarray:
    mats = [I2] * N
    mats[a] = op
    out = mats[0]
    for m in mats[1:]:
        out = np.kron(out, m)
    return out


# total S_z eigenvalue of each computational basis state, for sector selection
SZ_DIAG = np.round(
    np.real(np.diag(sum(_one_site(Z, i) for i in range(N)) / 2.0))
).astype(int)
SECTOR_IDX = np.flatnonzero(SZ_DIAG == MAGNETIZATION_SECTOR)


def _lowest_in_sector(ham: np.ndarray) -> np.ndarray:
    """Lowest eigenstate of H restricted to the total-S_z = MAGNETIZATION_SECTOR
    block. H conserves total S_z, so this is an exact eigenstate of H."""
    sub = ham[np.ix_(SECTOR_IDX, SECTOR_IDX)]
    _, vecs = np.linalg.eigh(sub)
    psi = np.zeros(DIM, dtype=complex)
    psi[SECTOR_IDX] = vecs[:, 0]
    return psi


def ground_state(j: float, rng: np.random.Generator | None = None) -> np.ndarray:
    ham = np.zeros((DIM, DIM), dtype=complex)
    for i, op in enumerate(BOND_OPS):
        coupling = 1.0 if i % 2 == 0 else j
        if rng is not None:
            coupling *= rng.uniform(1.0 - DISORDER, 1.0 + DISORDER)
        ham += coupling * op
    return _lowest_in_sector(ham)


def ground_state_from_couplings(couplings: np.ndarray) -> np.ndarray:
    ham = np.zeros((DIM, DIM), dtype=complex)
    for coupling, op in zip(couplings, BOND_OPS):
        ham += float(coupling) * op
    return _lowest_in_sector(ham)


def random_global_rotation(rng: np.random.Generator) -> np.ndarray:
    """r^{(x)N} for a Haar-random single-qubit SU(2) element r.

    Applied per sample. Commutes with every S_i . S_j, so it changes the state
    without changing the label or any invariant bond correlator.
    """
    a = rng.normal(size=4)
    a /= np.linalg.norm(a)
    r = a[0] * I2 - 1j * (a[1] * X + a[2] * Y + a[3] * Z)
    out = r
    for _ in range(N - 1):
        out = np.kron(out, r)
    return out


def sample_instance() -> tuple[np.ndarray, float, float]:
    """Draw one disordered ring; label by the REALIZED stronger sublattice.

    v2.1 lesson (probe ladder): labeling by nominal j while disorder can flip
    which sublattice actually ends up stronger injects irreducible label noise
    near criticality — at (j<=0.97, d=0.40) EVERY probe circuit, including the
    exact SU(2)+dimer reference, collapsed to the same ~0.72 accuracy. The
    physical question is unchanged (which bond sublattice is dimerized), but it
    must be asked of the sampled Hamiltonian, not of the nominal parameter.
    Samples with realized gap < GAP_MIN are rejected, so no sample is
    intrinsically ambiguous; |gap| is the difficulty dial for grouping.

    Returns (couplings, label, gap).
    """
    while True:
        logj = RNG.uniform(np.log(J_OUTER), np.log(1.0 / J_OUTER))
        j = float(np.exp(logj))
        couplings = np.array([
            (1.0 if i % 2 == 0 else j) * RNG.uniform(1.0 - DISORDER, 1.0 + DISORDER)
            for i in range(N)
        ])
        gap = float(np.mean(couplings[1::2]) - np.mean(couplings[0::2]))
        if abs(gap) < GAP_MIN:
            continue
        return couplings, (1.0 if gap > 0 else -1.0), gap


def site_state_to_qubit_state(psi: np.ndarray) -> np.ndarray:
    """Reorder tensor factors from site labeling to scrambled qubit labeling."""
    t = psi.reshape([2] * N)
    # site s occupies axis s; we want qubit q axis order where q = RELABEL[s]
    # destination axis for source axis s is QUBIT_RELABEL[s]
    dest = list(QUBIT_RELABEL)
    t = np.moveaxis(t, list(range(N)), dest)
    return t.reshape(DIM)


J_OUTER = 0.75   # nominal-j band edge; band includes the critical point, the
                 # GAP_MIN rejection (not a j window) removes ambiguous samples


def difficulty_groups(gaps: np.ndarray) -> np.ndarray:
    """Quartile bins of the realized sublattice gap |gap|: 0 = hardest quartile.

    Shipped under the neutral name group_<split>; the evaluator scores the
    WORST group's mean margin so a candidate cannot coast on easy samples.
    """
    d = np.abs(gaps)
    qs = np.quantile(d, [0.25, 0.5, 0.75])
    return np.digitize(d, qs).astype(np.int8)


def uniform_bond_zz(psi: np.ndarray) -> float:
    """Mean over ring bonds of <Z_a Z_b> (site labeling). The v1/v2 readout;
    kept only as a diagnostic — it is NOT rotation invariant."""
    return float(np.mean([
        np.real(psi.conj() @ two_site(Z, a, b) @ psi) for a, b in BONDS
    ]))


def uniform_bond_dot_observable() -> np.ndarray:
    """The two-qubit readout operator (X@X + Y@Y + Z@Z)/3, as a 4x4 matrix.

    Shipped in the dataset so the backend never names it. Symmetric under
    exchanging the two qubits, so the wire order at the measurement site
    cannot matter.
    """
    m = (np.kron(X, X) + np.kron(Y, Y) + np.kron(Z, Z)) / 3.0
    assert np.allclose(m, m.conj().T)
    return m


def uniform_bond_dot(psi: np.ndarray) -> float:
    """The v3 FIXED readout on the raw state: mean over ring bonds of
    <X_a X_b + Y_a Y_b + Z_a Z_b> / 3. Commutes with global rotations, so an
    equivariant circuit conjugates it into another invariant."""
    return float(np.mean([
        np.real(psi.conj() @ op @ psi) / 3.0 for op in BOND_OPS
    ]))


def main() -> None:
    sizes = {"train": 60, "validation": 300, "test": 600}
    splits = {}
    for name, size in sizes.items():
        need = {1.0: size // 2, -1.0: size - size // 2}
        states, labels, gaps = [], [], []
        while sum(need.values()) > 0:
            couplings, label, gap = sample_instance()
            if need[label] <= 0:
                continue  # exact class balance by rejection
            need[label] -= 1
            psi = ground_state_from_couplings(couplings)
            # v3: independent random global spin frame per sample.
            psi = random_global_rotation(RNG) @ psi
            states.append(site_state_to_qubit_state(psi))
            labels.append(label)
            gaps.append(gap)
        splits[name] = (
            np.stack(states).astype(np.complex128),
            np.array(labels),
            np.array(gaps),
        )
        print(f"{name}: {size} states, balance {np.mean(np.array(labels) > 0):.2f}, "
              f"|gap| range [{np.abs(gaps).min():.3f}, {np.abs(gaps).max():.3f}]")

    # identity-baseline sanity check (site labeling, pre-scramble readout):
    probe_js = np.concatenate([np.linspace(0.2, 0.8, 8), np.linspace(1.25, 5, 8)])
    ys = [uniform_bond_dot(ground_state(j)) for j in probe_js]
    print("identity-circuit uniform-bond readout by j:")
    for j, y in zip(probe_js, ys):
        print(f"  j={j:5.2f}  mean<S.S>/3={y:+.4f}")
    lo = np.array(ys[:8]); hi = np.array(ys[8:])
    print(f"class means: j<1 {lo.mean():+.4f}  j>1 {hi.mean():+.4f} "
          f"(should be ~equal -> identity baseline near chance)")

    # v3 invariance check: the shipped readout must be blind to the random
    # frame, and the old ZZ readout must not be.
    check_rng = np.random.default_rng(99)
    couplings, _, _ = sample_instance()
    psi0 = ground_state_from_couplings(couplings)
    dots, zzs = [], []
    for _ in range(6):
        psi_r = random_global_rotation(check_rng) @ psi0
        dots.append(uniform_bond_dot(psi_r))
        zzs.append(uniform_bond_zz(psi_r))
    print(f"frame check over 6 random rotations of one state:\n"
          f"  invariant readout <S.S>: spread {np.ptp(dots):.2e} "
          f"(must be ~0)  mean {np.mean(dots):+.4f}\n"
          f"  v1/v2 readout   <ZZ>  : spread {np.ptp(zzs):.2e} "
          f"(must be O(1))  mean {np.mean(zzs):+.4f}")

    np.savez_compressed(
        HERE / "dataset.npz",
        x_train=splits["train"][0], y_train=splits["train"][1],
        x_validation=splits["validation"][0], y_validation=splits["validation"][1],
        x_test=splits["test"][0], y_test=splits["test"][1],
        group_validation=difficulty_groups(splits["validation"][2]),
        group_test=difficulty_groups(splits["test"][2]),
        readout_pairs=np.array(
            [[int(QUBIT_RELABEL[a]), int(QUBIT_RELABEL[b])] for a, b in BONDS],
            dtype=np.int8),
        # The readout observable travels as an unlabelled matrix so that no file
        # the proposer can read states which operator it is. Written here rather
        # than in the backend because the backend is readable: the contextualized
        # arm shows its seed in full, and in the zero-context arm the evolve
        # block is arbitrary Python and can import the backend.
        pair_observable=uniform_bond_dot_observable(),
    )
    (HERE / "answer_key.json").write_text(json.dumps({
        "dataset_version": "v3-2026-07-29",
        "magnetization_sector": MAGNETIZATION_SECTOR,
        "global_frame_randomized": True,
        "readout": "mean over ring bonds of (XX+YY+ZZ)/3, SU(2) invariant",
        "task": "bond-alternating Heisenberg XXX ring N=8, dimer phase label",
        "symmetry": ["global SU(2): tied RXX=RYY=RZZ per pair",
                     "bond alternation: even/odd bond structure"],
        "qubit_relabel": QUBIT_RELABEL.tolist(),
        "bonds_site_order": BONDS,
        "labeling": "realized stronger sublattice (mean odd vs even realized coupling)",
        "j_band": [J_OUTER, 1.0 / J_OUTER],
        "disorder": DISORDER,
        "gap_min": GAP_MIN,
        "gap_train": splits["train"][2].tolist(),
        "gap_validation": splits["validation"][2].tolist(),
        "gap_test": splits["test"][2].tolist(),
    }, indent=2))
    print("saved dataset.npz + answer_key.json (local only)")


if __name__ == "__main__":
    main()
