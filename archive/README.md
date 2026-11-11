# Archive

Material from this project that the report in `../README.md` does not use.
Nothing here is referenced by the report's figures, tables or numbers; it is
kept so the earlier work stays reconstructible.

| path | what it is |
|---|---|
| `tic-tac-toe/` | T1, the tic-tac-toe symmetry task the project started from |
| `transfer-su2/` | T3, the SU(2) Hamiltonian transfer task |
| `zc-sn/`, `zc-su2/`, `zc-ttt/` | zero-context run variants of the three tasks |
| `final-report-draft.md` | earlier draft of the report, superseded by `../README.md` |
| azure scripts | `launch_azure_ens.sh`, `resume_azure_ens.sh`, `orch_azure.sbatch`, `patch_azure_client.py`, `add_azure_pricing.py`, `fix_azure_pricing_flags.py` — the Azure-routed `az_*` arms, replaced by the OpenRouter arms the report uses |
| `launch_ens3.sh`, `ens3_status.sh` | the earlier `ens3` ensemble, predating the weak/mid/frontier split |
| `structural_exec.py`, `run_structural_exec.sh`, `sym_snapshot.sh` | S_8 structural analysis written for the `az_*` arms; the report's labels come from `../analysis/labelling/` instead |
| `build_zero_context.py`, `write_activate.py`, `ZERO-CONTEXT.md` | the zero-context task builder |
| dated notes | `2026-08-14-direction.md`, `202608-18-direction.md`, `2026-08-19-meeting.md`, `2026-08-24-labelling.md`, `2026-08-25-prompts`, `frontier-resume.md`, `noticing-structure`, `writeup-ideas.md`, `OPERATING_MANUAL.md` |
| PDFs | `2509.24978v5.pdf`, `2606.24808v1.pdf`, `Fellowship Report 2026.pdf`/`.pages` |

The T1 and T3 run databases live here, so rebuilding `../viz/data/` against
`experiments/` alone drops those runs from the viewer. See `../viz/README.md`.
