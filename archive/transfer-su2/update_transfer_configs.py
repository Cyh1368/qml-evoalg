#!/usr/bin/env python3
"""Rewrite the contextualized (transfer) arm's task message for v3.

The v1 text was factually wrong after the v2/v3 architecture changes: it
claimed 6 block repetitions with independent parameter copies (the code does 3
with shared parameters) and described the readout as a Z-Z correlator (the
readout observable now ships as an opaque matrix in the dataset). It also
described the v1 economy-dominated scoring rather than the current one.

The readout is described here as "supplied by the dataset", which is exactly
what it now is, and which keeps this arm contextualized without stating the
structure the search is supposed to discover.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

TASK_SYS_MSG = """
You are an expert in variational quantum circuit design.

Goal:
Evolve the ANSATZ_SPEC for an 8-qubit classifier of quantum states.
The fixed code will train each candidate with Adam in a simulated PennyLane
circuit.

Fixed architecture:
- 8 qubits.
- Each input is a precomputed 8-qubit state vector from the dataset, prepared
  with StatePrep.
- The candidate ansatz block is applied 3 times in sequence, with the SAME
  parameter values in every repetition: the trainable parameter count equals
  the number of distinct param names.
- Readout: a fixed two-qubit observable supplied by the dataset, measured on a
  fixed set of qubit pairs also supplied by the dataset, averaged into one
  scalar and passed through a trainable gain and bias, regressed to the +1/-1
  label.

Only edit the EVOLVE-BLOCK, especially ANSATZ_SPEC. Do not change the fixed
training loop, dataset handling, measurements, or block count.

Formal ANSATZ_SPEC schema:
- Single-qubit parametrized gates:
  {"gate": "RX"|"RY"|"RZ", "wire": int 0..7, "param": "name"}
- Fixed two-qubit gates:
  {"gate": "CNOT"|"CZ", "wires": [first, second]}
- Parametrized two-qubit gates:
  {"gate": "CRX"|"CRY"|"CRZ", "wires": [control, target], "param": "name"}
  {"gate": "XX"|"YY"|"ZZ", "wires": [a, b], "param": "name"}   # Ising-type rotations

Connectivity: two-qubit gates may act on ANY pair of distinct qubits.

Parameter sharing:
Reusing the same param string shares that parameter within one ansatz block.
Use sharing deliberately: it is the only way to reduce the parameter count
without removing gates.

Starting point:
The seed block applies independent RY and RZ rotations on every qubit, a line
of CZ gates, and a final RZ layer.

Candidate quality:
The score is dominated by ROBUST SEPARATION: validation samples are grouped by
hidden difficulty, and the largest score term is the margin of the WORST group,
so the classifier must separate the hardest samples, not just the average ones.
The training set is very small, and held-out behaviour is the only thing that
counts: fitting the training set is a poor predictor of the score, so structures
that generalize from few examples win. Parameter economy matters at every count:
fewer distinct trainable parameter names ALWAYS scores higher, with no point of
diminishing returns. Also reduce the train-test gap and converge in fewer steps.

Invalid candidates are rejected for unsupported gates, bad wires, non-finite
metrics, or too many parameters.
"""

for path in sorted(HERE.glob("shinka_config_*.json")):
    conf = json.loads(path.read_text())
    conf["evo"]["task_sys_msg"] = TASK_SYS_MSG
    conf["evo"]["max_api_costs"] = 12.0
    # Match the zero-context arm: 5.x models reject non-default temperatures,
    # and holding temperature fixed across arms keeps the two variants
    # comparable on everything except how much context the proposer gets.
    conf["evo"]["llm_kwargs"]["temperatures"] = [1.0]
    path.write_text(json.dumps(conf, indent=2))
    print(f"updated {path.name}: model={conf['evo']['llm_models']} "
          f"cap=${conf['evo']['max_api_costs']}")
