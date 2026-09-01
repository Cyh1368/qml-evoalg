# Analysis

Everything that turns the run databases in `../experiments/` into the numbers
and figures quoted in `../README.md`.

## `labelling/` — the circuit and patch-note labels

Reads `../../viz/data/run_sn-transfer-*.js` and emits the label tables:

```bash
python3 analysis/labelling/label_circuits.py   # -> labels.json       (circuit structure)
python3 analysis/labelling/label_notes.py      # -> note_labels.json  (patch-note regexes)
python3 analysis/labelling/stats.py            # -> stats.json
python3 analysis/labelling/note_stats.py       # -> note_stats.json
python3 analysis/labelling/build_report.py         # -> symmetry_report.html
python3 analysis/labelling/build_notes_report.py   # -> patch_notes_report.html
```

Run them in that order; each step reads the previous step's JSON. The two HTML
reports are standalone browsable pages — open them directly in a browser.

## `report/` — the figures and statistics in the report

Self-contained: `report/data/` holds a frozen copy of the label tables and the
task dataset, so these two scripts reproduce the report without touching the
run databases.

```bash
python3 analysis/report/compute_stats.py   # every statistic quoted in the report
python3 analysis/report/make_figures.py    # regenerates analysis/report/figures/
```

Both need `numpy`, `matplotlib` and `scipy`; in this repository they run under
`viz/.venv_render/bin/python`. `report/figures/` mirrors the root `figures/`
directory that the report embeds.

Note: `report/stats_output.txt` is an older capture, taken before from-scratch
runs were truncated to 20 generations. The report quotes the current output of
`compute_stats.py` (563 proposals), not this file (704).
