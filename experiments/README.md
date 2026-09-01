# Experiments

The S_n graph-connectedness runs behind the report in `../README.md`.

| path | what it is |
|---|---|
| `transfer-sn/` | the task itself: `make_dataset.py`, `dataset.npz`, `evaluate.py`, `initial_program.py` (the seed ansatz), `baseline_program.py` (the hand-designed S_8-equivariant circuit), the `shinka_config_*.json` ensemble configs, and one `results_*/` directory per run holding its `programs.sqlite` |
| `transfer-sn/null/` | the null-control arm, trained on a different dataset — its scores are **not** on the same axis as the main runs (see `../viz/README.md`) |
| `launch_or_ens.sh` | submits the weak/mid/frontier OpenRouter arms as Slurm jobs (run on the cluster login node) |
| `sync_or_runs.sh` | pulls finished run databases back down and rebuilds both viewers (run locally) |
| `export_results.py`, `run_export.sh` | export every run to CSV for replication |

Run directories are named `results_or_<arm>_r<n>` for the from-scratch arms and
carry an `e1`/`rw` infix for the continued and ablation arms. `build_data.py`
derives each run's viewer slug from these directory names, so renaming one
renames its run in the viewer.
