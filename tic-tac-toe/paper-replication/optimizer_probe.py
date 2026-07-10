"""Feasibility + timing probe for candidate optimizers on the cemoid L=3,P=2 cost.

For each optimizer: run a few real gradient steps (batch 15) from a fixed seed,
record whether it runs, whether the loss decreases, and seconds/step.
This determines which optimizers are usable and feeds the runtime estimate.
"""
import sys, time, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pennylane as qml
from pennylane import numpy as pnp
from sweep import (make_circuit, l2_loss, _batch_indices, build_data_splits,
                   N_CEMOID_PARAMS, TRAIN_SIZE, VALIDATION_SIZE, TEST_SIZE,
                   DATA_SEED, LEARNING_RATE, BATCH_SIZE)

L, P, SEED, N_STEPS = 3, 2, 0, 12

def make_opt(name):
    lr = LEARNING_RATE
    return {
        "GradientDescent": lambda: qml.GradientDescentOptimizer(lr),
        "Momentum":        lambda: qml.MomentumOptimizer(lr),
        "Nesterov":        lambda: qml.NesterovMomentumOptimizer(lr),
        "Adagrad":         lambda: qml.AdagradOptimizer(lr),
        "RMSProp":         lambda: qml.RMSPropOptimizer(lr),
        "Adam":            lambda: qml.AdamOptimizer(lr),
        "QNG":             lambda: qml.QNGOptimizer(lr),
        "MomentumQNG":     lambda: qml.MomentumQNGOptimizer(lr),
        "QNSPSA":          lambda: qml.QNSPSAOptimizer(stepsize=lr),
        "Rotosolve":       lambda: qml.RotosolveOptimizer(),
        "SPSA":            lambda: qml.SPSAOptimizer(maxiter=300),
    }[name]()

def probe(name):
    splits = build_data_splits(seed=DATA_SEED, train_size=TRAIN_SIZE,
                               validation_size=VALIDATION_SIZE, test_size=TEST_SIZE, replace=True)
    x_train, y_train, _ = splits["train"]
    x_train = pnp.array(x_train, dtype=float, requires_grad=False)
    y_train = pnp.array(y_train, dtype=float, requires_grad=False)
    circuit = make_circuit(L, P)
    n_blocks = L * P
    rng = np.random.default_rng(SEED)
    params = pnp.array(rng.uniform(-0.05, 0.05, size=(n_blocks, N_CEMOID_PARAMS)), requires_grad=True)
    opt = make_opt(name)
    order = rng.permutation(len(x_train))
    def cost(p, bx, by): return l2_loss(circuit, p, bx, by)
    loss0 = float(cost(params, x_train, y_train))
    t0 = time.time(); ok_steps = 0
    for step in range(N_STEPS):
        ids = _batch_indices(order, step, BATCH_SIZE)
        bx, by = x_train[ids], y_train[ids]
        params = opt.step(lambda p: cost(p, bx, by), params)
        ok_steps += 1
    dt = time.time() - t0
    loss1 = float(cost(params, x_train, y_train))
    return dict(name=name, sec_per_step=dt/max(ok_steps,1), loss0=loss0, loss1=loss1,
                decreased=loss1 < loss0)

if __name__ == "__main__":
    names = ["GradientDescent","Momentum","Nesterov","Adagrad","RMSProp","Adam",
             "QNG","MomentumQNG","QNSPSA","Rotosolve","SPSA"]
    print(f"{'optimizer':>16} {'status':>8} {'s/step':>9} {'loss0->loss1':>22}")
    for n in names:
        try:
            r = probe(n)
            st = "OK" if r["decreased"] else "no-desc"
            print(f"{n:>16} {st:>8} {r['sec_per_step']:>9.3f} {r['loss0']:>9.4f} -> {r['loss1']:.4f}")
        except Exception as e:
            msg = f"{type(e).__name__}: {e}"
            print(f"{n:>16} {'FAIL':>8} {'-':>9}   {msg[:80]}")
