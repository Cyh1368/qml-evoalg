# qml-evoalg
This is the repo for Cheng-You's research project, Quantum Machine Learning Ansatz Optimization with Evolutionary Algorithms, under the guidance of Allen Mi.

## Run viewer

All ShinkaEvolve run results (34 runs across the three tasks) can be browsed
with the static web viewer in [`viz/`](viz/README.md):

```bash
cd viz && python3 -m http.server 8080   # then open http://localhost:8080
```

Evolutionary tree per run, per-node patch notes, circuit diagrams, metrics,
diffs, and lineage tracing. See `viz/README.md` for rebuilding the data or
using ShinkaEvolve's stock WebUI on the committed `programs.sqlite` files.

Task directories: `tic-tac-toe/` (T1), `*-sn/` (T2 graph), `*-su2/` (T3);
`zc-*` = zero-context arms, `transfer-*` = transfer/full-context arms.
