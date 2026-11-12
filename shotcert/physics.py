"""Physical tasks for ShotCert.

Both tasks return *exact* expectations so the deployed risk is enumerable; shot noise is added only
at deployment. The point of the design is that the symmetry failure has a physical mechanism rather
than being a synthetic perturbation of a label, and that the three regimes differ by *how much of the
odd response the target actually contains* — which is what "approximately symmetric" means.

Heisenberg response (physical primary)
--------------------------------------
Chain with bond-alternating exchange plus a staggered field of strength Delta, which is the one
control parameter that is odd under the chain mirror (for even n the mirror maps Delta -> -Delta).
The scientific target is a specified mixture of the mirror-even and mirror-odd parts of the
quenched site-0 response; a=0 asks for the even response, a=1 for the raw response, and the
intermediate regime is the realistic case where the target is mostly even but not exactly.

The deployed device mis-sets the field by a second-order rectification of the analog control line,
Delta_eff = Delta + c*Delta^2. That error is odd in Delta to leading order, which is precisely the
component that averaging over Delta -> -Delta cancels. A fixed-site readout bias would NOT be
cancelable by input averaging, and the module says so rather than pretending otherwise.

Cluster-Ising recognition (independent evaluation)
--------------------------------------------------
Different mechanism: a transverse-field cluster Hamiltonian whose ground-state string order is even
under the same kind of parameter-rectification error, used to test transfer rather than to tune.
"""

from __future__ import annotations

import numpy as np

from shotcert.core import Group, Task
from shotcert.qsim import eig_hermitian, neel_state, pauli_chain, two_site, unitary_from_eig


def _heis(n, J_alt):
    H = np.zeros((2 ** n, 2 ** n), dtype=complex)
    for b in range(n - 1):
        J = J_alt if b % 2 == 0 else 1.0
        for op in ("X", "Y", "Z"):
            H = H + J * two_site(n, b, b + 1, op)
    return H


def _stag(n):
    """Staggered field operator M = sum_i (-1)^i Z_i: odd under the chain mirror for even n."""
    M = np.zeros((2 ** n, 2 ** n), dtype=complex)
    for i in range(n):
        M = M + ((-1) ** i) * pauli_chain(n, i, "Z")
    return M


class HeisenbergResponse:
    """Exact and device-reported site-0 response of the quenched chain, cached by (t, Delta)."""

    def __init__(self, n=6, J_alt=1.3, c_rect=0.18, gamma=0.0):
        self.n = n
        self.H0 = _heis(n, J_alt)
        self.M = _stag(n)
        self.Z0 = pauli_chain(n, 0, "Z")
        self.psi0 = neel_state(n)
        self.c_rect = c_rect
        self.gamma = gamma
        self._cache = {}
        self._eig = {}                           # eigendecomposition cached per Delta
        self.evals = 0

    def _U(self, t, delta):
        key = round(float(delta), 7)
        hit = self._eig.get(key)
        if hit is None:
            hit = eig_hermitian(self.H0 + float(delta) * self.M)
            self._eig[key] = hit
        w, V = hit
        return unitary_from_eig(w, V, t)

    def exact(self, t, delta):
        """<Z_0>(t, Delta) under exact unitary dynamics."""
        key = (round(float(t), 7), round(float(delta), 7))
        hit = self._cache.get(key)
        if hit is not None:
            return hit
        psi = self._U(t, delta) @ self.psi0
        val = float(np.real(np.vdot(psi, self.Z0 @ psi)))
        if self.gamma > 0:                      # relaxation damps the measured polarisation
            val = val * (1.0 - self.gamma) ** self.n
        self._cache[key] = val
        self.evals += 1
        return val

    def device(self, t, delta):
        """What the hardware reports: the same experiment at the rectified field setting."""
        return self.exact(t, float(delta) + self.c_rect * float(delta) ** 2)


def heisenberg_task(n=6, a_odd=0.0, c_rect=0.18, J_alt=1.3, gamma=0.0, resp=None):
    """Target = (1-a)*even response + a*raw response; device = response at the rectified field."""
    R = resp or HeisenbergResponse(n=n, J_alt=J_alt, c_rect=c_rect, gamma=gamma)

    def _vec(fn, X):
        return np.array([fn(float(t), float(d)) for t, d in X], dtype=float)

    def label(x):
        X = np.atleast_2d(np.asarray(x, dtype=float))

        def one(t, d):
            r = R.exact(t, d)
            r_even = 0.5 * (R.exact(t, d) + R.exact(t, -d))
            return (1 - a_odd) * r_even + a_odd * r
        return _vec(one, X)

    def model(x):
        return _vec(R.device, np.atleast_2d(np.asarray(x, dtype=float)))

    def x_dist(m, rng):
        # Declared discretisation of the input distribution: t on a 48-point grid, Delta on a
        # 64-point grid symmetric about 0. Exact expectations at the sampled points; the grid
        # exists so the eigendecomposition cache is actually reused, and it is declared here
        # rather than fitted.
        tg = np.linspace(0.05, 1.5, 48)
        dg = np.linspace(-1.0, 1.0, 64)
        ti = rng.integers(0, len(tg), size=m)
        di = rng.integers(0, len(dg), size=m)
        return np.column_stack([tg[ti], dg[di]])

    def e(x):
        return np.asarray(x, dtype=float)

    def flip(x):
        x = np.asarray(x, dtype=float)
        out = x.copy()
        out[..., 1] = -out[..., 1]
        return out

    t = Task(name="heisenberg_n%d_a%.2f" % (n, a_odd), dim=2, label=label, model=model,
             x_dist=x_dist, group=Group("mirror_delta", (e, flip)),
             note="n=%d a_odd=%.2f c_rect=%.3f J_alt=%.2f gamma=%.3f" % (n, a_odd, c_rect, J_alt, gamma))
    ys = label(t.x_dist(120, np.random.default_rng(11)))
    t.y_var = float(np.var(ys))
    t.resp = R
    return t


class ClusterIsingResponse:
    """Independent evaluation task: transverse-field cluster Hamiltonian, string-order response.

    Different mechanism from the primary (four-body cluster term instead of two-body exchange), and
    the target is the even part of a string-order observable. Nothing here is tuned from the primary
    task's outcomes; the split is by task family, declared before generation.
    """

    def __init__(self, n=7, J=1.0, c_rect=0.15):
        self.n = n
        self.c_rect = c_rect
        dim = 2 ** n
        H0 = np.zeros((dim, dim), dtype=complex)
        # K_i = X_{i-1} Z_i X_{i+1}: three DIFFERENT sites, so the factors commute and K_i is
        # Hermitian. An earlier version put X and Z on the same site, which anticommute; the
        # product was non-Hermitian and the symmetrising eigensolver silently repaired it.
        for i in range(1, n - 1):
            H0 = H0 + J * (pauli_chain(n, i - 1, "X") @ pauli_chain(n, i, "Z")
                           @ pauli_chain(n, i + 1, "X"))
        self.H0 = H0
        self.M = _stag(n)
        # Local probe. A Z-string observable was tried first and returned exactly zero for every
        # initial state we could prepare cheaply (a multi-Z string has the wrong parity against both
        # the Neel state and |+..+>), which produced a task with identically zero risk. The
        # independence of this task comes from the three-body cluster Hamiltonian, not from the
        # observable, so a local probe is the honest choice.
        self.S = pauli_chain(n, 0, "Z")
        self.psi0 = neel_state(n)
        self._cache = {}
        self._eig = {}

    def exact(self, t, delta):
        key = (round(float(t), 7), round(float(delta), 7))
        hit = self._cache.get(key)
        if hit is not None:
            return hit
        ekey = round(float(delta), 7)
        if ekey not in self._eig:
            self._eig[ekey] = eig_hermitian(self.H0 + float(delta) * self.M)
        w, V = self._eig[ekey]
        psi = unitary_from_eig(w, V, t) @ self.psi0
        val = float(np.real(np.vdot(psi, self.S @ psi)))
        self._cache[key] = val
        return val

    def device(self, t, delta):
        return self.exact(t, float(delta) + self.c_rect * float(delta) ** 2)


def cluster_task(n=7, a_odd=0.0, c_rect=0.15, resp=None):
    R = resp or ClusterIsingResponse(n=n, c_rect=c_rect)

    def label(x):
        X = np.atleast_2d(np.asarray(x, dtype=float))
        out = []
        for t_, d in X:
            r = R.exact(t_, d)
            r_even = 0.5 * (R.exact(t_, d) + R.exact(t_, -d))
            out.append((1 - a_odd) * r_even + a_odd * r)
        return np.array(out)

    def model(x):
        X = np.atleast_2d(np.asarray(x, dtype=float))
        return np.array([R.device(float(t_), float(d)) for t_, d in X])

    def x_dist(m, rng):
        tg = np.linspace(0.05, 1.2, 40)
        dg = np.linspace(-1.0, 1.0, 64)
        ti = rng.integers(0, len(tg), size=m)
        di = rng.integers(0, len(dg), size=m)
        return np.column_stack([tg[ti], dg[di]])

    def e(x):
        return np.asarray(x, dtype=float)

    def flip(x):
        x = np.asarray(x, dtype=float)
        out = x.copy()
        out[..., 1] = -out[..., 1]
        return out

    t = Task(name="cluster_n%d_a%.2f" % (n, a_odd), dim=2, label=label, model=model,
             x_dist=x_dist, group=Group("mirror_delta", (e, flip)),
             note="n=%d a_odd=%.2f c_rect=%.3f" % (n, a_odd, c_rect))
    ys = label(t.x_dist(80, np.random.default_rng(13)))
    t.y_var = float(np.var(ys))
    t.resp = R
    return t
