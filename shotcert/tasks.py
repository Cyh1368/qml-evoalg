"""Task mechanisms for ShotCert: a 2-qubit control with three predeclared regimes, and a
bond-alternating Heisenberg response with non-covariant readout as the physical primary.

Everything here returns *exact* expectations, so the deployed risk is enumerable and the theory can
be checked against truth. Shot noise is added only at the deployment step (core.predict_once).
"""

from __future__ import annotations

import math

import numpy as np

from shotcert.core import Group, Task


# --------------------------------------------------------------------- control
def control_task(a_asym=None, c_break=0.35, regime="help", n_dim=2):
    """Two-qubit control. Label y(phi) = cos(phi) + a*sin(phi); frozen model f = cos(phi + c*phi^2).

    The group is phi -> -phi. The label is invariant exactly when a = 0, and the model breaks the
    invariance through the c*phi^2 term. One family, three predeclared regimes:

      a = 0            orbit averaging removes model bias            -> averaging helps
      a < 0 aligned    the model's odd component matches the label's, so averaging throws away
                       signal that was helping                                       -> averaging hurts
      a small aligned  an interior weight beats both endpoints                        -> interior best

    The sign matters and is not a detail: f(phi) = cos(phi + c*phi^2) has odd part -c*phi^2*sin(phi),
    so a label with a*sin(phi) of the SAME sign as that odd part is better served by the raw model,
    and averaging over phi -> -phi removes signal rather than error.
    """
    a = {"help": 0.0, "hurt": -0.55, "interior": -0.12}[regime] if a_asym is None else a_asym

    def label(x):
        x = np.asarray(x, dtype=float)
        phi = x[..., 0]
        return np.cos(phi) + a * np.sin(phi)

    def model(x):
        x = np.asarray(x, dtype=float)
        phi = x[..., 0]
        return np.cos(phi + c_break * phi ** 2)

    def x_dist(n, rng):
        # phi in [-1.2, 1.2]; second coordinate is an inert nuisance feature
        return np.column_stack([rng.uniform(-1.2, 1.2, size=n), rng.normal(size=n)])

    def e(x):
        return np.asarray(x, dtype=float)

    def s(x):
        x = np.asarray(x, dtype=float)
        out = x.copy()
        out[..., 0] = -out[..., 0]
        return out

    t = Task(name="control_%s" % regime, dim=n_dim, label=label, model=model, x_dist=x_dist,
             group=Group("mirror", (e, s)),
             note="a=%.3f c=%.3f; label invariant iff a=0" % (a, c_break))
    ys = label(t.x_dist(4000, np.random.default_rng(7)))
    t.y_var = float(np.var(ys))
    return t


# --------------------------------------------------------------------- physics helpers
