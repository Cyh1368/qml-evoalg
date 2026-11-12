"""ShotCert core: deployed orbit-randomised predictors, their exact risk, and the decomposition.

Access model (docs/PROTOCOL.md §0): scalar single-copy shots, one labeled preparation per
calibration instance, no two-copy or shared-measurement primitives.

The deployed object is a *stochastic* predictor. For input x and orbit point g, the ansatz produces a
Born probability p_g(x); a policy draws k orbit points, spends S shots total, and outputs an estimate
of a weighted orbit mean. Because the output is random, the risk R_S includes its own measurement
variance, and the allocation (k, S/k, weights) changes *which risk we have*, not merely how well we
know it. That is the whole reason this module enumerates the exact risk instead of estimating it.

Decomposition proved here numerically rather than asserted (F1/F2 in the protocol):

    R_S(a) = Bias(a)^2 + V_G(a)/k + Sigma(a)/S

with Bias the orbit-mean model bias, V_G the variance of the per-orbit-point mean (killed by draws,
immune to shots) and Sigma the mean shot variance (killed by shots, immune to draws).
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field

import numpy as np


# --------------------------------------------------------------------- group action
@dataclass(frozen=True)
class Group:
    """Finite input-transformation group, closed under composition, with identity."""
    name: str
    actions: tuple           # each action maps x -> x, a bijection on the input space

    def __len__(self):
        return len(self.actions)


def sign_flip_group():
    """G = {e, s} with s: phi -> -phi. Cheap, exactly enumerable, physically a site exchange."""
    def e(x):
        return np.asarray(x, dtype=float)

    def s(x):
        x = np.asarray(x, dtype=float)
        out = x.copy()
        out[..., 0] = -out[..., 0]
        return out
    return Group("sign_flip", (e, s))


def rotation_group(m=4):
    """Cyclic group acting by phi -> phi + 2*pi*j/m."""
    acts = []
    for j in range(m):
        def make(j=j):
            def act(x, j=j):
                x = np.asarray(x, dtype=float)
                out = x.copy()
                out[..., 0] = out[..., 0] + 2.0 * math.pi * j / m
                return out
            return act
        acts.append(make())
    return Group("cyclic_%d" % m, tuple(acts))


# --------------------------------------------------------------------- tasks
@dataclass
class Task:
    """A regression task: exact label y(x), model response f(x), and the measured observable.

    ``label`` is the target the deployed predictor is scored against; ``model`` is the frozen
    trained ansatz response, which may break symmetries the label respects. Both live on the same
    outcome scale as the measurement, so no unit conversion happens later.
    """
    name: str
    dim: int
    label: object
    model: object
    x_dist: object                       # callable(n, rng) -> (n, dim) samples
    group: Group
    y_var: float = 1.0                   # declared scale, used for epsilon
    note: str = ""


def born_prob(expectation):
    """Map a [-1, 1] observable expectation to the Born probability of the +1 outcome."""
    return np.clip(0.5 * (1.0 + np.asarray(expectation, dtype=float)), 1e-12, 1 - 1e-12)


def shot_variance(p):
    """Variance of the single-shot estimator 2*Bernoulli(p) - 1, which is 4p(1-p)."""
    p = np.asarray(p, dtype=float)
    return 4.0 * p * (1.0 - p)


def shot_var_from_mu(mu):
    """Same quantity written on the expectation scale: with p = (1+mu)/2, 4p(1-p) = 1 - mu^2.

    Everything in this module is analysed in expectation space, because the deployed estimator and
    the label both live on the +-1 outcome scale. Mixing the two is a real bug, not a notation
    choice: the first version of this code took the mean in probability space and the variance in
    expectation space, and the Monte-Carlo test caught it.
    """
    mu = np.asarray(mu, dtype=float)
    return 1.0 - mu ** 2


# --------------------------------------------------------------------- policies
@dataclass(frozen=True)
class Policy:
    """a = (orbit set, k draws, total shots S, weights, allocation).

    ``mode``:
      "raw"        -- always the identity orbit point (baseline a0)
      "orbit_k"    -- k draws with replacement from the orbit, S/k shots each, equal weights
      "stratified" -- every orbit point gets S/|G| shots (equal-shot stratification)
      "mix"        -- weight w on the orbit-averaged prediction, 1-w on raw, same total S
      "shrink"     -- A2.6 generic baseline, NO group use: (1-gamma) * raw estimate, same S shots.
                      Shrinkage toward a declared constant (0.0) is the standard group-free way to
                      trade bias for variance, so it is the fair comparator for "does the group earn
                      its shots". It spends the same shots, compiles one circuit, switches zero times
                      and needs no calibration of the group at all.
    """
    name: str
    mode: str
    k: int = 1
    S: int = 1
    w: float = 1.0
    orbit_size: int = 2
    gamma: float = 0.0     # shrink mode only: shrinkage coefficient toward the declared constant

    @property
    def shots_used(self):
        """Actual shots consumed by one deployment. Budget feasibility means shots_used <= S.

        The integer division S//k silently breaks feasibility when k > S: per becomes 1 and the
        deployment spends k shots while claiming S. That inflates every comparison at small S, and
        it is exactly the matched-budget violation this study exists to avoid, so it is checked in
        properties rather than remembered.
        """
        G = self.orbit_size
        if self.mode == "raw":
            return self.S
        # max(..., 1) is deliberate: it reports what a naive implementation would actually spend
        # when the division underflows, which is the failure this property exists to expose.
        if self.mode == "stratified":
            return G * max(self.S // G, 1)
        if self.mode == "mix":
            S_a = max(int(round(self.w * self.S)), 0)
            S_0 = max(self.S - S_a, 0)
            return G * max(S_a // G, 1) + S_0
        if self.mode == "shrink":
            return self.S
        return self.k * max(self.S // self.k, 1)

    def feasible(self):
        """Feasible means spendable within S *and* every term actually receives shots.

        A stratified or mixture policy at S < |G| would give some orbit point zero shots, which is a
        different (and undefined) estimator rather than a cheaper one. Such policies are excluded
        from the menu at that budget, and the exclusion is reported, not hidden.
        """
        if self.shots_used > self.S:
            return False
        G = self.orbit_size
        if self.mode == "stratified":
            return self.S // G >= 1
        if self.mode == "mix":
            S_a = max(int(round(self.w * self.S)), 0)
            S_0 = max(self.S - S_a, 0)
            # Both branches must be funded. Rounding can starve one of them: S=2, w=0.75 gives
            # S_a=2 and S_0=0, and the raw branch keeps weight 0.25 while receiving no shots, which
            # reached the estimator as a division by zero. A mixture that cannot fund a branch is not
            # a cheaper mixture, it is a different estimator, so it is excluded and reported.
            if not ((S_a // G) >= 1 or self.w == 0.0):
                return False
            return S_0 >= 1 or self.w == 1.0
        if self.mode == "orbit_k":
            return self.S // self.k >= 1
        return True

    @property
    def circuits(self):
        """Distinct circuits compiled: one per orbit point actually touched.

        Bounded by the orbit, always. The previous `min(k, orbit_size * 4)` reported eight distinct
        circuits for a two-element group, and the switching experiment charged that number; the
        reported interior optimum in k was an artefact of charging circuits that cannot exist. With
        |G| = 2 every k >= 2 compiles the same two circuits, so a per-circuit cost cannot produce an
        interior optimum at all --- only a per-SWITCH cost can, and switches are counted separately
        from an explicit schedule below.
        """
        if self.mode in ("raw", "shrink"):
            return 1
        if self.mode == "stratified":
            return self.orbit_size
        return min(self.k, self.orbit_size)

    @property
    def circuit_ids(self):
        """A3.2: the identity of the circuits this policy needs, so a menu can share them.

        A circuit here is an orbit point of the model, so two policies that read the same orbit point
        with the same shot count compile it once. Summing p.circuits over a menu charged twelve
        circuits for a two-element group; the distinct count is what a compilation budget pays.
        """
        G = self.orbit_size
        if self.mode in ("raw", "shrink"):
            return frozenset({0})
        if self.mode in ("stratified", "mix"):
            return frozenset(range(G))
        return frozenset(range(min(self.k, G)))

    @property
    def max_switches(self):
        """Circuit-setting changes in one prediction's shot sequence, under the sorted schedule.

        Schedule: the k chosen orbit indices in nondecreasing order (all shots for one circuit
        before moving on). Switches = number of adjacent pairs that differ, so a grouped schedule
        costs (distinct circuits touched - 1) and an interleaved schedule costs (k - 1). Reported
        as the grouped value, which is the minimum over schedules and therefore the most
        favourable-to-the-policy choice.
        """
        return max(self.circuits - 1, 0)


def orbit_expectations(task, x, orbit=None):
    """Exact observable expectation mu_g = E[shot | g, x] at every orbit point, in group order."""
    acts = task.group.actions if orbit is None else orbit
    out = []
    for act in acts:
        v = np.asarray(task.model(act(x)), dtype=float).reshape(-1)
        out.append(float(v[0]) if v.size == 1 else v)
    return np.asarray(out, dtype=float)


def orbit_probs(task, x, orbit=None):
    """Born probabilities at every orbit point (sampling space)."""
    return born_prob(orbit_expectations(task, x, orbit))


# --------------------------------------------------------------------- exact risk
def exact_risk(task, pol, xs, n_draw_enumerate=None):
    """Exact deployed risk R_S(a) = E[(Z_a(X) - Y)^2], enumerated over draws and shot outcomes.

    For each input the orbit-point probabilities are known exactly, so the estimator is a linear
    combination of independent binomial means whose mean and variance are available in closed form.
    Enumerating outcomes is unnecessary and slow; enumerating *draws* is unnecessary too for equal
    weights, but we keep the option because the verification test compares the closed form against a
    draw-enumerated version, and that comparison is the point.
    """
    xs = np.atleast_2d(np.asarray(xs, dtype=float))
    tot = 0.0
    for x in xs:
        mu = orbit_expectations(task, x)              # (|G|,)
        y = float(np.asarray(task.label(x), dtype=float).reshape(-1)[0])
        m, v = _estimator_moments(mu, pol)
        tot += (m - y) ** 2 + v
    return tot / len(xs)


def _estimator_moments(mu, pol):
    """Mean and variance of the deployed estimator Z given the exact orbit probabilities p.

    Written out because the factors of k are where an error hides: with k iid draws, S/k shots per
    draw and weights 1/k, the shot term is

        sum_j (1/k)^2 * sigma_j^2 / (S/k)  =  mean_j sigma_j^2 / S,

    independent of k, while the group-draw term is Var_g[mu_g] / k. That is protocol fact F1: at
    fixed total shots the split costs nothing in shot variance, so only the draw term moves.
    """
    G = len(mu)
    sv = shot_var_from_mu(mu)
    if pol.mode == "raw":
        return float(mu[0]), float(sv[0]) / pol.S
    if pol.mode == "shrink":
        g = float(pol.gamma)
        return (1.0 - g) * float(mu[0]), ((1.0 - g) ** 2) * float(sv[0]) / pol.S
    if pol.mode == "stratified":
        per = pol.S // G
        assert per >= 1, "infeasible policy reached the estimator"
        # estimate = (1/G) sum_j mean_j, each mean_j over `per` shots
        v = float(np.sum(sv)) / (G * G * per)
        return float(np.mean(mu)), v
    if pol.mode == "mix":
        # w on the *stratified* orbit average (S_a shots), 1-w on raw (S_0 shots)
        S_a = max(int(round(pol.w * pol.S)), 0)
        S_0 = max(pol.S - S_a, 0)
        per = S_a // G
        assert per >= 1 or pol.w == 0.0, "infeasible mixture reached the estimator"
        assert S_0 >= 1 or pol.w == 1.0, "mixture with an unfunded raw branch reached the estimator"
        m = pol.w * float(np.mean(mu)) + (1 - pol.w) * float(mu[0])
        v = 0.0
        if pol.w > 0.0 and per >= 1:        # at w=0 the orbit branch is absent, not free
            v += (pol.w ** 2) * float(np.sum(sv)) / (G * G * per)
        if pol.w < 1.0 and S_0 >= 1:        # at w=1 the raw branch is absent, not free
            v += ((1 - pol.w) ** 2) * float(sv[0]) / S_0
        return m, v
    # orbit_k
    per = pol.S // pol.k
    assert per >= 1, "infeasible policy reached the estimator"
    m = float(np.mean(mu))
    v_g = float(np.var(mu)) / pol.k
    v_s = float(np.mean(sv)) / (pol.k * per)
    return m, v_g + v_s


def components(task, xs, pol):
    """The three components of the protocol decomposition, evaluated on one input set.

    Returns (bias^2, V_G, Sigma) with R_S(a) = bias^2 + V_G/k + Sigma/S, where the integer-division
    factors are kept so the identity can be tested exactly rather than approximately.
    """
    xs = np.atleast_2d(np.asarray(xs, dtype=float))
    b2 = vg = sg = 0.0
    G = len(task.group.actions)
    for x in xs:
        p = orbit_expectations(task, x)
        sv = shot_var_from_mu(p)
        y = float(np.asarray(task.label(x), dtype=float).reshape(-1)[0])
        if pol.mode == "shrink":
            g = float(pol.gamma)
            b2 += ((1.0 - g) * float(p[0]) - y) ** 2
            vg += 0.0
            sg += ((1.0 - g) ** 2) * float(sv[0])
        elif pol.mode == "raw":
            b2 += (float(p[0]) - y) ** 2
            vg += 0.0
            sg += float(sv[0])
        elif pol.mode == "mix":
            S_a = max(int(round(pol.w * pol.S)), 0)
            S_0 = max(pol.S - S_a, 0)
            per = max(S_a // G, 1)     # components() is only called on feasible policies
            b2 += (pol.w * float(np.mean(p)) + (1 - pol.w) * float(p[0]) - y) ** 2
            vg += 0.0
            if pol.w > 0.0 and per >= 1:
                sg += (pol.w ** 2) * float(np.sum(sv)) * pol.S / (G * G * per)
            if pol.w < 1.0 and S_0 >= 1:
                sg += ((1 - pol.w) ** 2) * float(sv[0]) * pol.S / S_0
        else:
            per = max(pol.S // (pol.k if pol.mode == "orbit_k" else G), 1)  # components: feasible only
            denom = (pol.k * per) if pol.mode == "orbit_k" else (G * per)
            b2 += (float(np.mean(p)) - y) ** 2
            vg += float(np.var(p)) if pol.mode == "orbit_k" else 0.0
            sg += float(np.mean(sv)) * pol.S / denom
    n = len(xs)
    return b2 / n, vg / n, sg / n


def predict_once(task, x, pol, rng):
    """One deployed prediction: draw orbit points, spend shots, return the estimate."""
    G = len(task.group.actions)
    P = born_prob(orbit_expectations(task, x))
    if pol.mode == "raw":
        return 2.0 * (rng.binomial(pol.S, float(P[0])) / pol.S) - 1.0
    if pol.mode == "shrink":
        z0 = 2.0 * (rng.binomial(pol.S, float(P[0])) / pol.S) - 1.0
        return (1.0 - float(pol.gamma)) * z0
    if pol.mode == "stratified":
        per = pol.S // G
        assert per >= 1, "infeasible policy reached deployment"
        acc = 0.0
        for g in range(G):
            acc += 2.0 * (rng.binomial(per, float(P[g])) / per) - 1.0
        return acc / G
    if pol.mode == "mix":
        # w on the stratified orbit average, 1-w on raw; identical to _estimator_moments("mix")
        S_a = max(int(round(pol.w * pol.S)), 0)
        S_0 = max(pol.S - S_a, 0)
        per = S_a // G
        assert per >= 1 or pol.w == 0.0, "infeasible mixture reached deployment"
        if pol.w == 0.0:
            return 2.0 * (rng.binomial(pol.S, float(P[0])) / pol.S) - 1.0
        acc = 0.0
        for g in range(G):
            acc += 2.0 * (rng.binomial(per, float(P[g])) / per) - 1.0
        z_a = acc / G
        if pol.w >= 1.0:
            return z_a
        z_0 = 2.0 * (rng.binomial(S_0, float(P[0])) / S_0) - 1.0
        return pol.w * z_a + (1 - pol.w) * z_0
    idx = rng.integers(0, G, size=pol.k)
    per = pol.S // pol.k
    assert per >= 1, "infeasible policy reached deployment"
    acc = 0.0
    for j in idx:
        acc += 2.0 * (rng.binomial(per, float(P[int(j)])) / per) - 1.0
    return acc / pol.k


def orbit_prob_matrix(task, xs):
    """Born probabilities at every orbit point: shape (n_inputs, |G|)."""
    xs = np.atleast_2d(np.asarray(xs, dtype=float))
    return np.stack([born_prob(task.model(act(xs))) for act in task.group.actions], axis=1)


def orbit_mu_matrix(task, xs):
    """Exact expectations at every orbit point: shape (n_inputs, |G|)."""
    xs = np.atleast_2d(np.asarray(xs, dtype=float))
    return np.stack([np.asarray(task.model(act(xs)), dtype=float).reshape(-1)
                     for act in task.group.actions], axis=1)


def label_vector(task, xs):
    xs = np.atleast_2d(np.asarray(xs, dtype=float))
    return np.asarray(task.label(xs), dtype=float).reshape(-1)


def predict_batch(task, xs, pol, rng, reps=1):
    """Vectorised deployment: (reps, n_inputs) estimates of the deployed predictor.

    This is the same estimator as predict_once, written so that Monte-Carlo checks of the exact risk
    run in milliseconds rather than minutes. Keeping one implementation of the sampling logic and
    testing it against the exact formula is the guard against the analyzed-estimator and
    deployed-estimator drift that invalidated earlier work.
    """
    P = orbit_prob_matrix(task, xs)                    # (n, G)
    n, G = P.shape
    sv_shape = (reps, n)
    if pol.mode == "raw":
        cnt = rng.binomial(pol.S, np.broadcast_to(P[:, 0], sv_shape))
        return 2.0 * (cnt / pol.S) - 1.0
    if pol.mode == "stratified":
        per = pol.S // G
        assert per >= 1, "infeasible policy reached batch deployment"
        acc = np.zeros(sv_shape)
        for g in range(G):
            cnt = rng.binomial(per, np.broadcast_to(P[:, g], sv_shape))
            acc += 2.0 * (cnt / per) - 1.0
        return acc / G
    if pol.mode == "mix":
        S_a = max(int(round(pol.w * pol.S)), 0)
        S_0 = max(pol.S - S_a, 0)
        per = S_a // G
        assert per >= 1 or pol.w == 0.0, "infeasible mixture reached batch deployment"
        if pol.w == 0.0:
            cnt = rng.binomial(pol.S, np.broadcast_to(P[:, 0], sv_shape))
            return 2.0 * (cnt / pol.S) - 1.0
        acc = np.zeros(sv_shape)
        for g in range(G):
            cnt = rng.binomial(per, np.broadcast_to(P[:, g], sv_shape))
            acc += 2.0 * (cnt / per) - 1.0
        z_a = acc / G
        if pol.w >= 1.0:
            return z_a
        cnt0 = rng.binomial(S_0, np.broadcast_to(P[:, 0], sv_shape))
        z_0 = 2.0 * (cnt0 / S_0) - 1.0
        return pol.w * z_a + (1 - pol.w) * z_0
    per = pol.S // pol.k
    assert per >= 1, "infeasible policy reached batch deployment"
    idx = rng.integers(0, G, size=(reps, n, pol.k))
    acc = np.zeros(sv_shape)
    for j in range(pol.k):
        pj = np.take_along_axis(np.broadcast_to(P, (reps, n, G)), idx[:, :, j:j + 1], axis=2)[:, :, 0]
        cnt = rng.binomial(per, pj)
        acc += 2.0 * (cnt / per) - 1.0
    return acc / pol.k
