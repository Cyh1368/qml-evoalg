# Where the perm-motif was actually proposed

Every proposal in the six main arms (real / null x weak / mid / frontier) whose
circuit code contains the perm-motif (`tied-8`: one parameter driving
single-qubit gates on all 8 wires). Detection is the same `measure()` /
`spec_of()` code `build_run_metrics.py` uses, so these rows reconcile with the
`first gen` column of `RUN_METRICS.md`.

**Authored vs inherited.** A proposal is *authored* if its parent program did
not already contain the motif, so this proposal introduced it. Once the motif
is in a lineage it propagates by inheritance, and RUN_METRICS' `builds
perm-motif %` counts both kinds. The table below lists the authored events:
these are the generations where an ensemble genuinely proposed the
permutation-invariant construct. Patch text is ignored, as asked; the
`said perm` column is recorded only for reference.

## Summary

| task | arm | proposals containing motif | authored (introduced it) | runs with >=1 authored event | earliest authored gen |
|---|---|---:|---:|---:|---:|
| real | weak | 46 | 25 | 11 | 1 |
| real | mid | 37 | 21 | 7 | 2 |
| real | frontier | 60 | 15 | 3 | 3 |
| null | weak | 14 | 10 | 3 | 3 |
| null | mid | 14 | 11 | 4 | 2 |
| null | frontier | 4 | 4 | 3 | 1 |

## Authored events, one row per proposal

| task | arm | run | gen | model | patch name | score | said perm |
|---|---|---|---:|---|---|---:|---|
| real | weak | `weak_e1_r1` | 12 | openai/gpt-5.4-nano | `ansatz_reupload_rxglobal_crx_mix` | 0.1426 | no |
| real | weak | `weak_e1_r1` | 16 | openai/gpt-5.4-nano | `sharedmix_crx_rxglobal` | 0.1376 | no |
| real | weak | `weak_e1_r5` | 10 | openai/gpt-5.4-nano | `shared_global_singlequbit_params_fewerparams` | 0.5487 | no |
| real | weak | `weak_e1_r5` | 19 | openai/gpt-5.4-nano | `shared_prepost_cr_entanglers` | 0.1944 | no |
| real | weak | `weak_e1_r6` | 5 | openai/gpt-5.4-nano | `shared_ring_crz_block` | 0.4412 | no |
| real | weak | `weak_e1_r6` | 10 | openai/gpt-5.4-nano | `shared_nonlin_crz_ring_mix` | 0.4927 | no |
| real | weak | `weak_e1_r6` | 11 | openai/gpt-5.4-nano | `none` | 0.4937 | no |
| real | weak | `weak_e1_r6` | 13 | openai/gpt-5.4-nano | `shared_ring_crz_out_rz` | 0.2205 | no |
| real | weak | `weak_e1_r7` | 17 | google/gemini-3.1-flash-lite-preview | `lean_global_phase_ansatz` | 0.4542 | no |
| real | weak | `weak_e1_r7` | 18 | google/gemini-3.1-flash-lite-preview | `efficient_ladder_ansatz` | -0.6373 | no |
| real | weak | `weak_e1_r8` | 3 | openai/gpt-5.4-nano | `shared_ring_entangling_reupload_net` | -1.3147 | no |
| real | weak | `weak_e1_r9` | 3 | openai/gpt-5.4-nano | `shared_rz_entangling_crz_ansatz` | 0.2008 | no |
| real | weak | `weak_e1_r9` | 12 | openai/gpt-5.4-nano | `share_ry_rz_parity_plus_chain` | 0.3081 | no |
| real | weak | `weak_r1` | 14 | qwen/qwen3-coder | `add_rx_pre_layer` | 0.1192 | no |
| real | weak | `weak_r1` | 17 | openai/gpt-5.4-nano | `sharedrzcrzring_v2_globalz` | 0.1704 | no |
| real | weak | `weak_r1` | 34 | openai/gpt-5.4-nano | `banked_rx_rz_cz_shared` | 0.3920 | no |
| real | weak | `weak_r2` | 1 | openai/gpt-5.4-nano | `compact_shared_crz_ring` | 0.1281 | no |
| real | weak | `weak_r2` | 18 | openai/gpt-5.4-nano | `parityshare_ringcz_crx_gated` | 0.1998 | no |
| real | weak | `weak_r3` | 2 | openai/gpt-5.4-nano | `none` | -0.7263 | no |
| real | weak | `weak_r4` | 41 | qwen/qwen3-coder | `layered_entanglement_sharing` | 0.3376 | no |
| real | weak | `weak_r4` | 49 | google/gemini-3.1-flash-lite-preview | `ansatz_final_rx_layer_and_cz_optimization` | 0.0848 | no |
| real | weak | `weak_r5` | 5 | openai/gpt-5.4-nano | `compact_rz_layers_shared_final` | -0.0440 | no |
| real | weak | `weak_r5` | 12 | openai/gpt-5.4-nano | `compact_evenodd_rz_rx_cz` | 0.1391 | no |
| real | weak | `weak_r5` | 33 | openai/gpt-5.4-nano | `rx_czladder_evenodd_rzpost` | 0.1391 | no |
| real | weak | `weak_r5` | 35 | openai/gpt-5.4-nano | `shared_rzring_crz2param` | -0.7293 | no |
| real | mid | `mid_e1_r1` | 2 | anthropic/claude-haiku-4.5 | `shared_params_enhanced_entanglement` | -0.6054 | no |
| real | mid | `mid_e1_r1` | 8 | google/gemini-3-flash-preview | `symmetric_brick_longrange` | -1.6617 | no |
| real | mid | `mid_e1_r1` | 16 | openai/gpt-5.4-mini | `lean_global_bottleneck` | 0.3320 | no |
| real | mid | `mid_e1_r2` | 3 | openai/gpt-5.4-mini | `parity_symmetric_mixer_entangler` | -0.6556 | no |
| real | mid | `mid_e1_r2` | 11 | anthropic/claude-haiku-4.5 | `collapsed_rz_param_sharing` | -0.8075 | no |
| real | mid | `mid_e1_r3` | 2 | anthropic/claude-haiku-4.5 | `alternating_pair_entangle_shared` | 0.6888 | no |
| real | mid | `mid_e1_r3` | 3 | openai/gpt-5.4-mini | `brickwork_shared_mixer` | 0.1169 | no |
| real | mid | `mid_e1_r3` | 9 | anthropic/claude-haiku-4.5 | `adopt_best_param_sharing_pattern` | 0.6888 | no |
| real | mid | `mid_e1_r3` | 13 | google/gemini-3-flash-preview | `cyclic_crz_cry_hybrid_ansatz` | 0.4259 | no |
| real | mid | `mid_e1_r3` | 14 | openai/gpt-5.4-mini | `paritycry_ring` | 0.2991 | no |
| real | mid | `mid_e1_r3` | 17 | openai/gpt-5.4-mini | `axis_alternation_shared_layers` | 0.3661 | no |
| real | mid | `mid_e1_r4` | 4 | anthropic/claude-haiku-4.5 | `efficient-shared-crz-ansatz` | 0.0709 | no |
| real | mid | `mid_e1_r4` | 12 | anthropic/claude-haiku-4.5 | `interleaved_crz_entangling_with_shared_params` | 0.5385 | no |
| real | mid | `mid_e1_r5` | 19 | google/gemini-3-flash-preview | `symmetric_axis_mixing_ansatz` | -1.0479 | no |
| real | mid | `mid_r2` | 2 | openai/gpt-5.4-mini | `butterfly_message_passing` | 0.4025 | no |
| real | mid | `mid_r2` | 10 | openai/gpt-5.4-mini | `butterfly_shared_mixer` | 0.4025 | no |
| real | mid | `mid_r2` | 36 | anthropic/claude-haiku-4.5 | `hierarchical_mosaic_ansatz` | 0.3204 | no |
| real | mid | `mid_r2` | 37 | openai/gpt-5.4-mini | `butterfly_compact` | 0.4379 | no |
| real | mid | `mid_r2` | 40 | anthropic/claude-haiku-4.5 | `revert_hybrid_crx_improved` | 0.4443 | no |
| real | mid | `mid_r3` | 31 | google/gemini-3-flash-preview | `ring_connectivity_with_global_phase` | 0.3206 | no |
| real | mid | `mid_r3` | 49 | google/gemini-3-flash-preview | `global_twirl_ansatz` | 0.2765 | no |
| real | frontier | `frontier_e1_r1` | 3 | openai/gpt-5.6-sol | `collective_complete_graph` | 0.7840 | yes |
| real | frontier | `frontier_e1_r1` | 5 | openai/gpt-5.6-sol | `equivariant_collective_twist` | 0.7840 | yes |
| real | frontier | `frontier_e1_r1` | 9 | openai/gpt-5.6-sol | `symmetric_collective_decoder` | 0.8867 | yes |
| real | frontier | `frontier_e1_r1` | 11 | openai/gpt-5.6-sol | `collective_interleaved_twist` | 0.8462 | yes |
| real | frontier | `frontier_e1_r1` | 12 | openai/gpt-5.6-sol | `balanced_shared_crz` | 0.7347 | yes |
| real | frontier | `frontier_e1_r1` | 13 | openai/gpt-5.6-sol | `shared_dense_crz` | 0.4906 | no |
| real | frontier | `frontier_e1_r1` | 14 | openai/gpt-5.6-sol | `collective_interleaved_k8` | 0.8462 | yes |
| real | frontier | `frontier_e1_r1` | 16 | anthropic/claude-opus-4.6 | `interleaved_collective_rotations_4param` | 0.4658 | no |
| real | frontier | `frontier_e1_r2` | 3 | openai/gpt-5.6-sol | `cube_echo_channels` | 0.3342 | no |
| real | frontier | `frontier_e1_r2` | 5 | openai/gpt-5.6-sol | `equivariant_global_mixers` | 0.1529 | yes |
| real | frontier | `frontier_e1_r2` | 13 | openai/gpt-5.6-sol | `sparse_multiscale_decoder` | 0.2688 | no |
| real | frontier | `frontier_r1` | 3 | openai/gpt-5.6-sol | `shared_cube_mixer` | 0.4477 | no |
| real | frontier | `frontier_r1` | 5 | openai/gpt-5.6-sol | `symmetric_graph_mixer` | 0.7840 | yes |
| real | frontier | `frontier_r1` | 12 | openai/gpt-5.6-sol | `factorized_complete_graph` | 0.7840 | yes |
| real | frontier | `frontier_r1` | 14 | openai/gpt-5.6-sol | `collective_complete_graph_mixer` | 0.9832 | yes |
| null | weak | `null_weak_r1` | 3 | openai/gpt-5.4-nano | `none` | 1.2784 | no |
| null | weak | `null_weak_r1` | 6 | google/gemini-3.1-flash-lite-preview | `parameter_efficient_entangled_ansatz` | 1.0575 | no |
| null | weak | `null_weak_r2` | 5 | openai/gpt-5.4-nano | `cz_more_connectivity_shared_final_rz` | 1.2723 | no |
| null | weak | `null_weak_r2` | 17 | google/gemini-3.1-flash-lite-preview | `hybrid_entanglement_shared_rz` | 1.5016 | no |
| null | weak | `null_weak_r5` | 5 | openai/gpt-5.4-nano | `sharedrz_crz_ring_8q_reupload` | 1.4493 | no |
| null | weak | `null_weak_r5` | 13 | openai/gpt-5.4-nano | `none` | 1.3223 | no |
| null | weak | `null_weak_r5` | 14 | openai/gpt-5.4-nano | `shared_rz_czring_sparsecrz_reuploadfriendly` | 1.4493 | no |
| null | weak | `null_weak_r5` | 15 | qwen/qwen3-coder | `none` | 1.2284 | no |
| null | weak | `null_weak_r5` | 17 | openai/gpt-5.4-nano | `finalrz_shared_reduction` | 1.4049 | no |
| null | weak | `null_weak_r5` | 19 | qwen/qwen3-coder | `enhanced_ansatz_with_ring_coupling` | 1.1696 | no |
| null | mid | `null_mid_r1` | 18 | anthropic/claude-haiku-4.5 | `add_shared_rz_readout_layer` | 1.3700 | no |
| null | mid | `null_mid_r1` | 19 | anthropic/claude-haiku-4.5 | `add_shared_final_rz_layer` | 1.3700 | no |
| null | mid | `null_mid_r2` | 3 | anthropic/claude-haiku-4.5 | `efficient_ansatz_with_parameter_sharing` | -0.5246 | no |
| null | mid | `null_mid_r3` | 13 | google/gemini-3-flash-preview | `efficient_circular_cry` | 1.4945 | no |
| null | mid | `null_mid_r4` | 2 | anthropic/claude-haiku-4.5 | `parametrized_entangling_with_shared_output` | 1.3716 | no |
| null | mid | `null_mid_r4` | 7 | anthropic/claude-haiku-4.5 | `try_cry_gates_shared_rz` | 1.4313 | no |
| null | mid | `null_mid_r4` | 9 | anthropic/claude-haiku-4.5 | `ladder_topology_minimal` | 1.3613 | no |
| null | mid | `null_mid_r4` | 13 | anthropic/claude-haiku-4.5 | `alternating_cry_crx_shared_rz` | 1.4429 | no |
| null | mid | `null_mid_r4` | 16 | anthropic/claude-haiku-4.5 | `simplify_to_proven_pattern` | 1.5062 | no |
| null | mid | `null_mid_r4` | 18 | google/gemini-3-flash-preview | `efficient_shared_parametrized_entangler` | 1.3629 | no |
| null | mid | `null_mid_r4` | 19 | openai/gpt-5.4-mini | `shared_crz_skip_mixer` | 1.1754 | no |
| null | frontier | `null_frontier_r1` | 2 | openai/gpt-5.6-sol | `collective_phase_mixers` | -1.2218 | yes |
| null | frontier | `null_frontier_r2` | 1 | openai/gpt-5.6-sol | `symmetric_collective_mixer` | -1.1297 | yes |
| null | frontier | `null_frontier_r2` | 5 | openai/gpt-5.6-sol | `collective_xy_reupload` | -1.1740 | yes |
| null | frontier | `null_frontier_r3` | 5 | openai/gpt-5.6-sol | `qaoa_ring_mixer` | 1.3460 | no |

## First authored event per run

Runs absent from this table never produced the motif.

| task | arm | run | first gen with motif | authored there? | model |
|---|---|---|---:|---|---|
| real | weak | `weak_e1_r1` | 12 | yes | openai/gpt-5.4-nano |
| real | weak | `weak_e1_r5` | 10 | yes | openai/gpt-5.4-nano |
| real | weak | `weak_e1_r6` | 5 | yes | openai/gpt-5.4-nano |
| real | weak | `weak_e1_r7` | 17 | yes | google/gemini-3.1-flash-lite-preview |
| real | weak | `weak_e1_r8` | 3 | yes | openai/gpt-5.4-nano |
| real | weak | `weak_e1_r9` | 3 | yes | openai/gpt-5.4-nano |
| real | weak | `weak_r1` | 14 | yes | qwen/qwen3-coder |
| real | weak | `weak_r2` | 1 | yes | openai/gpt-5.4-nano |
| real | weak | `weak_r3` | 2 | yes | openai/gpt-5.4-nano |
| real | weak | `weak_r4` | 41 | yes | qwen/qwen3-coder |
| real | weak | `weak_r5` | 5 | yes | openai/gpt-5.4-nano |
| real | mid | `mid_e1_r1` | 2 | yes | anthropic/claude-haiku-4.5 |
| real | mid | `mid_e1_r2` | 3 | yes | openai/gpt-5.4-mini |
| real | mid | `mid_e1_r3` | 2 | yes | anthropic/claude-haiku-4.5 |
| real | mid | `mid_e1_r4` | 4 | yes | anthropic/claude-haiku-4.5 |
| real | mid | `mid_e1_r5` | 19 | yes | google/gemini-3-flash-preview |
| real | mid | `mid_r2` | 2 | yes | openai/gpt-5.4-mini |
| real | mid | `mid_r3` | 31 | yes | google/gemini-3-flash-preview |
| real | frontier | `frontier_e1_r1` | 3 | yes | openai/gpt-5.6-sol |
| real | frontier | `frontier_e1_r2` | 3 | yes | openai/gpt-5.6-sol |
| real | frontier | `frontier_r1` | 3 | yes | openai/gpt-5.6-sol |
| null | weak | `null_weak_r1` | 3 | yes | openai/gpt-5.4-nano |
| null | weak | `null_weak_r2` | 5 | yes | openai/gpt-5.4-nano |
| null | weak | `null_weak_r5` | 5 | yes | openai/gpt-5.4-nano |
| null | mid | `null_mid_r1` | 18 | yes | anthropic/claude-haiku-4.5 |
| null | mid | `null_mid_r2` | 3 | yes | anthropic/claude-haiku-4.5 |
| null | mid | `null_mid_r3` | 13 | yes | google/gemini-3-flash-preview |
| null | mid | `null_mid_r4` | 2 | yes | anthropic/claude-haiku-4.5 |
| null | frontier | `null_frontier_r1` | 2 | yes | openai/gpt-5.6-sol |
| null | frontier | `null_frontier_r2` | 1 | yes | openai/gpt-5.6-sol |
| null | frontier | `null_frontier_r3` | 5 | yes | openai/gpt-5.6-sol |

## Intentionality of the authored events

Denominator is the authored events above: the proposal introduced the perm-motif
into a lineage that did not have it. An event counts as **intentional** if the
`PERM` regex of `RUN_METRICS.md` (equivarian*, permut*, orbit*, exchangeab*,
relabel*, interchange*, S_8, S_n) fires on the proposal's own `patch_name` +
`patch_description`. The looser `says any-symmetry` and `says mirror` regexes
are shown alongside, same definitions, same denominator.

| task | arm | authored events | intentional (says perm) | % | says any-symmetry | % | says mirror | % |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| real | weak | 25 | 0 | 0.0 | 1 | 4.0 | 0 | 0.0 |
| real | mid | 21 | 0 | 0.0 | 10 | 47.6 | 4 | 19.0 |
| real | frontier | 15 | 10 | 66.7 | 12 | 80.0 | 0 | 0.0 |
| null | weak | 10 | 0 | 0.0 | 3 | 30.0 | 0 | 0.0 |
| null | mid | 11 | 0 | 0.0 | 2 | 18.2 | 0 | 0.0 |
| null | frontier | 4 | 3 | 75.0 | 3 | 75.0 | 0 | 0.0 |

Only the frontier arm authors the motif intentionally: 10/15 on the real task
and 3/4 on the null task name permutation symmetry in the patch that introduces
it. Weak and mid never do, on either task, in any of the 67 authored events
they produced. Their motif introductions are compression edits: the patch text
argues parameter efficiency and the tied-8 structure falls out of it.

The `says any-symmetry` column is not a softer version of the same signal. In
the mid arm the 10 any-symmetry hits are 4 mirror/butterfly labels
(`butterfly_shared_mixer`, `butterfly_compact`) plus vague uses of the bare word
symmetric (`symmetric_brick_longrange`, `parity_symmetric_mixer_entangler`,
`symmetric_axis_mixing_ansatz`), none of which describe the S_8 structure the
patch actually shipped. Counting them as intent would credit a wrong or empty
label for a correct build.

Three frontier real-task events are motif introductions with no symmetry word at
all (`cube_echo_channels`, `sparse_multiscale_decoder`, and one Opus patch,
`interleaved_collective_rotations_4param`), and two more name symmetry only
vaguely (`shared_cube_mixer`, `shared_dense_crz`).


## Caveat: tied-8 is not the task's symmetry

The symmetry comes from the task, not the metric. `feature_map` in
`initial_program.py` encodes feature k as an `IsingZZ` on `FEATURE_PAIRS[k]`, and
those 28 pairs are exactly the edges of K8; the readout is the mean of `PauliZ`
over all 8 wires. Relabelling the qubits permutes wires and features together, so
the model is S_8-invariant exactly when the ansatz is, which needs two things:

1. every single-qubit **block** covers all 8 wires, and
2. every two-qubit **block** covers all 28 pairs (the complete graph).

A block is a maximal run of consecutive spec entries sharing one
(parameter, gate type) key. Blocks, not pooled families: a circuit applying 16 CZ
pairs, then RX/RY layers, then the other 12 has a pooled union of K8 but is not
invariant, since a relabelling moves the first block off itself. Two blocks of a
diagonal gate separated by a diagonal-only span do merge. The implementation is
`s8_parts()` in `build_run_metrics.py`.

`tied-8` tests neither condition. It fires when *some one* parameter drives
single-qubit gates on all 8 wires, a weak proxy for (1) and silent on (2), and is
neither necessary nor sufficient: `weak_e1_r1` gen 12 passes it on an `rx_global`
layer while its CZ line chain, disjoint-pair CRZ and `ry_low`/`ry_high` split all
break S_8; `frontier_e1_r1` gen 10 fails it while being fully invariant (one
parameter drives RY, RZ and RX layers, so the family has 24 gates, not 8).

The two conditions differ enormously in difficulty, which is the whole story:

| task | arm | proposals | tied-8 | ties all 8 wires | K8 entangler | S_8-invariant | of which real entangler |
|---|---|---:|---:|---:|---:|---:|---:|
| real | weak | 324 | 46 | 12 | 1 | 0 | 0 |
| real | mid | 192 | 37 | 10 | 0 | 0 | 0 |
| real | frontier | 86 | 60 | 56 | 24 | 23 | 22 |
| null | weak | 93 | 14 | 0 | 0 | 0 | 0 |
| null | mid | 93 | 14 | 1 | 0 | 0 | 0 |
| null | frontier | 42 | 4 | 3 | 3 | 3 | 1 |

Tying single-qubit rotations falls out of any parameter-reduction edit. Replacing
the seed's CZ line chain with all 28 pairs requires recognising that the features
are the edges of K8, and only the frontier arm does it. `real entangler` excludes
circuits passing vacuously with no two-qubit gate, which is 2 of the 3
null-frontier cases: the honest null-frontier count is 1.

Authored S_8-invariant circuits (parent not already invariant), all runs:

| task | run | gen | model | patch name | says perm |
|---|---|---:|---|---|---|
| real | `frontier_r1` | 5 | openai/gpt-5.6-sol | `symmetric_graph_mixer` | yes |
| real | `frontier_r1` | 9 | openai/gpt-5.6-sol | `orbit_twist` | yes |
| real | `frontier_r1` | 12 | openai/gpt-5.6-sol | `factorized_complete_graph` | yes |
| real | `frontier_r1` | 13 | openai/gpt-5.6-sol | `matching_ordered_complete_graph` | yes |
| real | `frontier_r1` | 14 | openai/gpt-5.6-sol | `collective_complete_graph_mixer` | yes |
| real | `frontier_r1` | 19 | google/gemini-3.1-pro-preview | `none` | no |
| real | `frontier_r1` | 20 | openai/gpt-5.6-sol | `complete_graph_two_axis` | yes |
| real | `frontier_e1_r1` | 3 | openai/gpt-5.6-sol | `collective_complete_graph` | yes |
| real | `frontier_e1_r1` | 5 | openai/gpt-5.6-sol | `equivariant_collective_twist` | yes |
| real | `frontier_e1_r1` | 9 | openai/gpt-5.6-sol | `symmetric_collective_decoder` | yes |
| real | `frontier_e1_r1` | 11 | openai/gpt-5.6-sol | `collective_interleaved_twist` | yes |
| real | `frontier_e1_r1` | 14 | openai/gpt-5.6-sol | `collective_interleaved_k8` | yes |
| real | `frontier_e1_r2` | 5 | openai/gpt-5.6-sol | `equivariant_global_mixers` | yes |
| null | `null_frontier_r1` | 2 | openai/gpt-5.6-sol | `collective_phase_mixers` | yes |
| null | `null_frontier_r2` | 1 | openai/gpt-5.6-sol | `symmetric_collective_mixer` | yes |
| null | `null_frontier_r2` | 5 | openai/gpt-5.6-sol | `collective_xy_reupload` | yes |

15 of these 16 name permutation symmetry. The exception is one
`google/gemini-3.1-pro-preview` patch with no patch name recorded. Every other
authored event is `openai/gpt-5.6-sol`.

The authored-event tables earlier in this document are keyed on tied-8 and so
list the wrong population for weak and mid. Their counts (25 and 21 on the real
task) are tied-layer introductions, not symmetry discoveries; neither arm ever
builds the entangler.

Correction history, in order. (1) tied-8 was described as "the S_8-invariant
construct" in `RUN_METRICS.md` and here; it is not. (2) The first circuit test
grouped gates by parameter alone and rejected a family spanning two gate types,
wrongly failing e.g. `frontier_r1` gen 39 where `collective_mid` drives a full RY
layer and a full RX layer; keying by (parameter, gate) fixed it. (3) That test
still pooled each family's wires over the whole circuit, which accepted 18
circuits whose CZ gates are split into partial blocks (the recurring 16+12 in
`frontier_r1`); the block rule above dropped real-frontier from 41 to 23. Figures
near 40 in any earlier draft came from the pooled test.

