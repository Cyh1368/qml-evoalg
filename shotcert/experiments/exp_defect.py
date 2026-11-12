"""A6.0: reproduce the third review's estimand defect as a durable artifact.

The number is measured, not remembered, so the manuscript sentence that quotes it can be generated.
"""
import json, os, time
import numpy as np
from shotcert.core import Policy, exact_risk, orbit_expectations, shot_var_from_mu
from shotcert.physics import heisenberg_task
from shotcert.record import identity_block_expected_loss, record_expected_loss

task = heisenberg_task(n=6, a_odd=1.0, c_rect=0.18)
G, s = len(task.group.actions), 8
S = s * G
xs = task.x_dist(400, np.random.default_rng(5))
strat = Policy("strat", "stratified", S=S, orbit_size=G)
a0 = Policy("a0", "raw", S=S, orbit_size=G)
a0w = Policy("a0w", "raw", S=s, orbit_size=G)
target = exact_risk(task, strat, xs) - exact_risk(task, a0, xs)
defective = record_expected_loss(task, strat, xs, S) - identity_block_expected_loss(task, a0w, xs, s)
sv = float(np.mean([shot_var_from_mu(np.asarray(orbit_expectations(task, x)))[0] for x in xs]))
out = {"created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
       "task": "heisenberg_raw_n6", "s": s, "S": S,
       "delta_deployed": target, "delta_calibration": defective,
       "offset_measured": defective - target, "offset_predicted": -sv / (2.0 * s),
       "sigma0_sq": sv, "ratio_offset_to_effect": abs(defective - target) / abs(target)}
os.makedirs("shotcert/results", exist_ok=True)
json.dump(out, open("shotcert/results/defect_a60.json", "w"), indent=1)
print("delta_deployed=%+.5f delta_calibration=%+.5f offset=%+.5f predicted=%+.5f ratio=%.1fx"
      % (target, defective, defective - target, -sv / (2.0 * s), out["ratio_offset_to_effect"]))
