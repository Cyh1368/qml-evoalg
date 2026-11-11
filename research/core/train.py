"""Candidate training on the frozen core interfaces (see INTERFACES.md).

Full-circuit readout ``f(x) = w . <O>(x) + b`` where ``<O>(x)`` are the task's
frozen diagonal observables measured after the per-example expanded circuit
(``candidates.expand_example``). Block parameters are trainable; the readout
weights ``w`` and bias ``b`` are trainable and initialised to zero. Block
parameters are initialised ``Uniform(-pi, pi)`` from ``seed``. Optimisation is
Adam on MSE with fixed ``steps`` (no early stopping); minibatches are drawn from
``seed``. Determinism: the same ``(candidate, task, x, y, seed, steps, batch,
lr)`` reproduces the loss history bitwise.

The forward pass and reverse-mode gradients use :mod:`research.core.simulator`
(``Forward.run`` / ``Forward.grad``), the reference path validated against
``simulator.unitary`` and central finite differences in ``test_simulator``.
Because the feature map is per-example, each example has its own expanded gate
list; compiled ``Forward`` objects are cached per row and reused across steps
(the gate structure is fixed, only the trainable parameter values change).
"""
from dataclasses import dataclass, field

import numpy as np

from research.core import candidates as _cand
from research.core import simulator as _sim

_INIT_HI = np.pi


def obs_matrix(observables, n):
    """Dense diagonal eigenvalue spectrum ``(k, 2**n)`` for the observable set."""
    d = 2 ** n
    bits = ((np.arange(d)[:, None] >> (n - 1 - np.arange(n))) & 1)
    out = np.zeros((len(observables), d))
    for r, obs in enumerate(observables):
        terms = list(obs.items()) if isinstance(obs, dict) else list(obs)
        for index, coeff in terms:
            sign = np.ones(d)
            for i in index:
                sign *= 1.0 - 2.0 * bits[:, int(i)]
            out[r] += float(np.real(coeff)) * sign
    return out


# --------------------------------------------------------- vectorised predict
# The feature map is per-example, but rows sharing the same expanded gate
# STRUCTURE (gate names/wires/param-vs-angle pattern) can be pushed through the
# circuit together if the feature-map (fixed-angle) gates are applied with
# per-row angle vectors. This makes full-validation-set risk evaluation orders
# of magnitude faster than a per-row Python loop; it is validated against the
# per-row reference path in test_train.py.
def _structure_key(gates):
    return tuple((g["gate"],
                  tuple(g["wires"]) if "wires" in g else (int(g["wire"]),),
                  g.get("param") if "param" in g else None,
                  None if "param" in g else ("A" if "angle" in g else "F"))
                 for g in gates)


def _apply_one_batch(psi, pauli, wire, angles, n):
    m, d = psi.shape
    ang = np.full(m, float(angles)) if np.isscalar(angles) else np.asarray(
        angles, float).reshape(-1)
    bc = (m,) + (1,) * (n - 1)
    c = np.cos(ang / 2.0).reshape(bc)
    s = np.sin(ang / 2.0).reshape(bc)
    v = np.moveaxis(psi.reshape((m,) + (2,) * n), wire + 1, 1)
    a0, a1 = v[:, 0].copy(), v[:, 1].copy()
    if pauli == 'X':
        v[:, 0] = c * a0 - 1j * s * a1
        v[:, 1] = -1j * s * a0 + c * a1
    elif pauli == 'Y':
        v[:, 0] = c * a0 - s * a1
        v[:, 1] = s * a0 + c * a1
    else:
        v[:, 0] = (c - 1j * s) * a0
        v[:, 1] = (c + 1j * s) * a1
    return np.moveaxis(v, 1, wire + 1).reshape(m, d)


def _apply_fixed_batch(psi, name, wire, n):
    m, d = psi.shape
    v = np.moveaxis(psi.reshape((m,) + (2,) * n), wire + 1, 1)
    a0, a1 = v[:, 0].copy(), v[:, 1].copy()
    if name == "H":
        v[:, 0] = (a0 + a1) / np.sqrt(2.0); v[:, 1] = (a0 - a1) / np.sqrt(2.0)
    elif name == "X":
        v[:, 0], v[:, 1] = a1, a0
    elif name == "Y":
        v[:, 0] = -1j * a1; v[:, 1] = 1j * a0
    elif name == "S":
        v[:, 1] = 1j * a1
    elif name == "T":
        v[:, 1] = np.exp(1j * np.pi / 4) * a1
    else:
        raise ValueError(name)
    return np.moveaxis(v, 1, wire + 1).reshape(m, d)


def _apply_two_batch(psi, name, wires, angles, n):
    m, d = psi.shape
    a, b = wires
    v = np.moveaxis(psi.reshape((m,) + (2,) * n), [a + 1, b + 1], [1, 2])
    if name in ("CNOT", "CZ"):
        if name == "CNOT":
            tmp = v[:, 1, 0].copy()
            v[:, 1, 0] = v[:, 1, 1]
            v[:, 1, 1] = tmp
        else:
            v[:, 1, 1] = -v[:, 1, 1]
        return np.moveaxis(v, [1, 2], [a + 1, b + 1]).reshape(m, d)
    ang = np.full(m, float(angles)) if np.isscalar(angles) else np.asarray(
        angles, float).reshape(-1)
    bc = (m,) + (1,) * (n - 2)
    cp = (np.cos(ang / 2.0) - 1j * np.sin(ang / 2.0)).reshape(bc)
    cm = (np.cos(ang / 2.0) + 1j * np.sin(ang / 2.0)).reshape(bc)
    if name == "RZZ":
        v[:, 0, 0] *= cp; v[:, 0, 1] *= cm; v[:, 1, 0] *= cm; v[:, 1, 1] *= cp
        return np.moveaxis(v, [1, 2], [a + 1, b + 1]).reshape(m, d)
    pauli = name[-1]
    c = np.cos(ang / 2.0).reshape(bc); s = np.sin(ang / 2.0).reshape(bc)
    b0, b1 = v[:, 1, 0].copy(), v[:, 1, 1].copy()
    if pauli == 'X':
        v[:, 1, 0] = c * b0 - 1j * s * b1; v[:, 1, 1] = -1j * s * b0 + c * b1
    elif pauli == 'Y':
        v[:, 1, 0] = c * b0 - s * b1; v[:, 1, 1] = s * b0 + c * b1
    else:
        v[:, 1, 0] = (c - 1j * s) * b0; v[:, 1, 1] = (c + 1j * s) * b1
    return np.moveaxis(v, [1, 2], [a + 1, b + 1]).reshape(m, d)


def batched_expectations(candidate, task, x, theta, obs=None):
    """Observable expectations ``(len(x), k)`` via structure-grouped batching."""
    x = np.asarray(x)
    n = int(candidate.get("n_qubits") or task.n_qubits)
    names = list(candidate.get("param_names") or [])
    pdict = _cand.param_dict(candidate, theta)
    if obs is None:
        obs = obs_matrix(task.observables, n)
    k = len(task.observables)
    m = len(x)
    out = np.zeros((m, k))
    groups = {}
    for i in range(m):
        gates, _ = _cand.expand_example(candidate, task, x[i])
        groups.setdefault(_structure_key(gates), []).append((i, gates))
    d = 2 ** n
    for key, members in groups.items():
        idxs = [i for i, _ in members]
        rep = members[0][1]
        mg = len(idxs)
        psi = np.zeros((mg, d), dtype=complex); psi[:, 0] = 1.0
        for pos, entry in enumerate(rep):
            name = entry["gate"]
            wires = ([int(entry["wire"])] if "wire" in entry
                     else [int(w) for w in entry["wires"]])
            if "param" in entry:
                angles = float(pdict[entry["param"]])
            elif "angle" in entry:
                angles = np.array([float(mm[1][pos]["angle"]) for mm in members])
            else:
                angles = 0.0
            if name in _sim._FIXED1:
                psi = _apply_fixed_batch(psi, name, wires[0], n)
            elif name in ("RX", "RY", "RZ"):
                psi = _apply_one_batch(psi, name[-1], wires[0], angles, n)
            elif name in ("CNOT", "CZ", "RZZ", "CRX", "CRY", "CRZ"):
                psi = _apply_two_batch(psi, name, wires, angles, n)
            else:
                raise ValueError("Unsupported gate %s" % name)
        out[idxs] = (np.abs(psi) ** 2) @ obs.T
    return out


@dataclass
class Fit:
    """A trained candidate: block parameters plus a linear readout."""
    candidate: dict
    task_name: str
    n_qubits: int
    param_names: list
    theta: np.ndarray
    w: np.ndarray
    b: float
    train_loss: float
    loss_history: np.ndarray = field(repr=False, default_factory=lambda: np.array([]))

    def _plans(self, task, x):
        obs = obs_matrix(task.observables, self.n_qubits)
        pdict = _cand.param_dict(self.candidate, self.theta)
        return obs, pdict

    def expectations(self, task, x):
        """Observable expectations ``(len(x), k)`` for rows ``x`` (batched)."""
        return batched_expectations(self.candidate, task, x, self.theta)

    def predict(self, task, x):
        x = np.asarray(x)
        E = self.expectations(task, x)
        return E @ self.w + self.b


def _zero_state(n):
    d = 2 ** n
    psi = np.zeros((1, d), dtype=complex)
    psi[0, 0] = 1.0
    return psi


def risk(fit, task, x, y):
    """Mean squared error of ``fit`` on rows ``x`` with targets ``y``."""
    pred = fit.predict(task, x)
    y = np.asarray(y, dtype=float).reshape(-1)
    return float(np.mean((pred - y) ** 2))


def _compile_plan(candidate, task, row):
    gates, names = _cand.expand_example(candidate, task, row)
    return _sim.compile_circuit(gates, list(candidate.get("param_names") or []),
                                int(candidate.get("n_qubits") or task.n_qubits))


def fit(candidate, task, x, y, seed, steps=200, batch=32, lr=0.05,
        max_train=None):
    """Train one candidate; see the module docstring for the estimator.

    ``max_train`` optionally caps the training pool by a seeded subsample (the
    search harness uses the full pool by default). Selection is on training data
    only; no validation rows are read here.
    """
    errors = _cand.validate(candidate, task)
    if errors:
        raise ValueError("cannot fit invalid candidate: %s" % errors)
    x = np.asarray(x)
    y = np.asarray(y, dtype=float).reshape(-1)
    if len(x) != len(y):
        raise ValueError("x/y length mismatch %d vs %d" % (len(x), len(y)))
    n = int(candidate.get("n_qubits") or task.n_qubits)
    names = list(candidate.get("param_names") or [])
    k = len(task.observables)
    obs = obs_matrix(task.observables, n)

    rng = np.random.default_rng(int(seed))
    if max_train is not None and 0 < int(max_train) < len(x):
        keep = np.sort(rng.choice(len(x), size=int(max_train), replace=False))
        x, y = x[keep], y[keep]
    m = len(x)
    batch = int(min(max(1, batch), m))

    theta = rng.uniform(-_INIT_HI, _INIT_HI, size=len(names))
    w = np.zeros(k)
    b = 0.0

    # Compile one Forward per row once; reused across all steps.
    plans = [_compile_plan(candidate, task, x[i]) for i in range(m)]

    # Adam state for the concatenated vector [theta, w, b].
    dim = len(names) + k + 1
    m1 = np.zeros(dim)
    m2 = np.zeros(dim)
    beta1, beta2, eps = 0.9, 0.999, 1e-8
    loss_history = np.zeros(int(steps))

    for step in range(int(steps)):
        idx = rng.choice(m, size=batch, replace=False)
        pdict = _cand.param_dict(candidate, theta)
        g = np.zeros(dim)
        sq = 0.0
        for i in idx:
            fwd = plans[i]
            psi, cache = fwd.run(theta, _zero_state(n))
            E = ((np.abs(psi) ** 2) @ obs.T).reshape(-1)
            f = float(E @ w + b)
            resid = f - float(y[i])
            sq += resid * resid
            coef = (2.0 / batch) * resid
            g[len(names):len(names) + k] += coef * E
            g[-1] += coef
            # dL/dpsi* for this row: psi * (dL/dE . obs_spectrum)
            dloss_dE = coef * w                     # (k,)
            dloss_dpsi = psi * (dloss_dE @ obs)     # (1, 2**n)
            g[:len(names)] += fwd.grad(theta, cache, dloss_dpsi)
        loss = sq / batch
        loss_history[step] = loss
        if not np.all(np.isfinite(g)):
            break
        t = step + 1
        m1 = beta1 * m1 + (1 - beta1) * g
        m2 = beta2 * m2 + (1 - beta2) * (g * g)
        mh = m1 / (1 - beta1 ** t)
        vh = m2 / (1 - beta2 ** t)
        upd = lr * mh / (np.sqrt(vh) + eps)
        theta = theta - upd[:len(names)]
        w = w - upd[len(names):len(names) + k]
        b = float(b - upd[-1])

    # final training loss on the (sub)sampled pool
    pdict = _cand.param_dict(candidate, theta)
    pred = np.array([float((((np.abs(plans[i].run(theta, _zero_state(n))[0]) ** 2)
                             @ obs.T).reshape(-1)) @ w + b) for i in range(m)])
    train_loss = float(np.mean((pred - y) ** 2))
    return Fit(candidate=candidate, task_name=str(getattr(task, "name", "")),
               n_qubits=n, param_names=names, theta=theta, w=w, b=b,
               train_loss=train_loss, loss_history=loss_history)
