# Ansatz gallery

Static page showing the actual gate structure of the `transfer-sn` circuits that
`../../transfer-sn/SEED_VS_BASELINE_REPORT.md` compares numerically:

| Entry | What it is |
|---|---|
| Seed ansatz | `initial_program.py` — 24 free angles/block, 146 params, no symmetry awareness |
| Hand-designed baseline | `baseline_program.py` — exactly S_8-equivariant, one angle per gate orbit, 20 params |
| Weak / mid / frontier ensemble best | highest-scoring correct program of `results_or_weak_r1`, `results_or_mid_r1`, `results_or_frontier_r1` |
| Frontier lineage | every node on the ancestor walk to the frontier winner, so the three significant score jumps (+0.784 at gen 5, +0.186 at gen 35, +0.230 at gen 77) can be read gate by gate |

Gates are colored by **parameter family**: gates sharing one trainable angle share
one color. That is the whole story of this task — tying a family across all 8 wires
(or all 28 pairs) is what makes a block permutation-equivariant, and every circuit
worth looking at here converged on 3 tied families / 20 parameters.

Only one ansatz *block* is drawn. The fixed architecture repeats it 3 uploads x 2
repeats with fresh angles each time, so total params = angles/block x 6 + 2 readout.

## View

```bash
cd viz/circuits
python3 -m http.server 8080   # then open http://localhost:8080
```

Opening `index.html` over `file://` also works — `circuits_data.js` is a plain
script assignment, not a `fetch`.

## Rebuild the data

`circuits_data.js` is generated from the task sources and the run databases. It
needs numpy only (to read `dataset.npz` for `FEATURE_PAIRS`); the render venv has it:

```bash
../.venv_render/bin/python build_circuits.py
```

The builder evaluates each program's `EVOLVE-BLOCK` in a sandbox namespace holding
only the problem constants, because several evolved programs build `ANSATZ_SPEC`
with comprehensions rather than assigning a literal.

Prose descriptions live in the `NOTES` object in `index.html`, not in the data file.

## Relation to `../index.html`

The parent viewer is the general run explorer (evolutionary tree, diffs, metrics
across all 3 tasks and ~38 runs). This page is the narrow, curated counterpart:
one task, nine circuits, focused on what the gate structure actually looks like.
