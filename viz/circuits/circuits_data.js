window.CIRCUITS = [
 {
  "key": "seed",
  "kind": "reference",
  "title": "Seed ansatz",
  "source": "experiments/transfer-sn/initial_program.py",
  "gates": [
   {
    "gate": "RY",
    "wires": [
     0
    ],
    "param": "ry_0"
   },
   {
    "gate": "RY",
    "wires": [
     1
    ],
    "param": "ry_1"
   },
   {
    "gate": "RY",
    "wires": [
     2
    ],
    "param": "ry_2"
   },
   {
    "gate": "RY",
    "wires": [
     3
    ],
    "param": "ry_3"
   },
   {
    "gate": "RY",
    "wires": [
     4
    ],
    "param": "ry_4"
   },
   {
    "gate": "RY",
    "wires": [
     5
    ],
    "param": "ry_5"
   },
   {
    "gate": "RY",
    "wires": [
     6
    ],
    "param": "ry_6"
   },
   {
    "gate": "RY",
    "wires": [
     7
    ],
    "param": "ry_7"
   },
   {
    "gate": "RZ",
    "wires": [
     0
    ],
    "param": "rz_pre_0"
   },
   {
    "gate": "RZ",
    "wires": [
     1
    ],
    "param": "rz_pre_1"
   },
   {
    "gate": "RZ",
    "wires": [
     2
    ],
    "param": "rz_pre_2"
   },
   {
    "gate": "RZ",
    "wires": [
     3
    ],
    "param": "rz_pre_3"
   },
   {
    "gate": "RZ",
    "wires": [
     4
    ],
    "param": "rz_pre_4"
   },
   {
    "gate": "RZ",
    "wires": [
     5
    ],
    "param": "rz_pre_5"
   },
   {
    "gate": "RZ",
    "wires": [
     6
    ],
    "param": "rz_pre_6"
   },
   {
    "gate": "RZ",
    "wires": [
     7
    ],
    "param": "rz_pre_7"
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     1
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     2
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     3
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     3,
     4
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     4,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     5,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     6,
     7
    ],
    "param": null
   },
   {
    "gate": "RZ",
    "wires": [
     0
    ],
    "param": "rz_post_0"
   },
   {
    "gate": "RZ",
    "wires": [
     1
    ],
    "param": "rz_post_1"
   },
   {
    "gate": "RZ",
    "wires": [
     2
    ],
    "param": "rz_post_2"
   },
   {
    "gate": "RZ",
    "wires": [
     3
    ],
    "param": "rz_post_3"
   },
   {
    "gate": "RZ",
    "wires": [
     4
    ],
    "param": "rz_post_4"
   },
   {
    "gate": "RZ",
    "wires": [
     5
    ],
    "param": "rz_post_5"
   },
   {
    "gate": "RZ",
    "wires": [
     6
    ],
    "param": "rz_post_6"
   },
   {
    "gate": "RZ",
    "wires": [
     7
    ],
    "param": "rz_post_7"
   }
  ],
  "stats": {
   "n_gates": 31,
   "n_params_per_block": 24,
   "n_params": 146,
   "families": [
    {
     "param": "ry_0",
     "gates": [
      "RY"
     ],
     "count": 1
    },
    {
     "param": "ry_1",
     "gates": [
      "RY"
     ],
     "count": 1
    },
    {
     "param": "ry_2",
     "gates": [
      "RY"
     ],
     "count": 1
    },
    {
     "param": "ry_3",
     "gates": [
      "RY"
     ],
     "count": 1
    },
    {
     "param": "ry_4",
     "gates": [
      "RY"
     ],
     "count": 1
    },
    {
     "param": "ry_5",
     "gates": [
      "RY"
     ],
     "count": 1
    },
    {
     "param": "ry_6",
     "gates": [
      "RY"
     ],
     "count": 1
    },
    {
     "param": "ry_7",
     "gates": [
      "RY"
     ],
     "count": 1
    },
    {
     "param": "rz_pre_0",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_pre_1",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_pre_2",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_pre_3",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_pre_4",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_pre_5",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_pre_6",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_pre_7",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_post_0",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_post_1",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_post_2",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_post_3",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_post_4",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_post_5",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_post_6",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_post_7",
     "gates": [
      "RZ"
     ],
     "count": 1
    }
   ]
  }
 },
 {
  "key": "baseline",
  "kind": "reference",
  "title": "Hand-designed S_8-equivariant baseline",
  "source": "experiments/transfer-sn/baseline_program.py",
  "gates": [
   {
    "gate": "RY",
    "wires": [
     0
    ],
    "param": "ry_all"
   },
   {
    "gate": "RY",
    "wires": [
     1
    ],
    "param": "ry_all"
   },
   {
    "gate": "RY",
    "wires": [
     2
    ],
    "param": "ry_all"
   },
   {
    "gate": "RY",
    "wires": [
     3
    ],
    "param": "ry_all"
   },
   {
    "gate": "RY",
    "wires": [
     4
    ],
    "param": "ry_all"
   },
   {
    "gate": "RY",
    "wires": [
     5
    ],
    "param": "ry_all"
   },
   {
    "gate": "RY",
    "wires": [
     6
    ],
    "param": "ry_all"
   },
   {
    "gate": "RY",
    "wires": [
     7
    ],
    "param": "ry_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     0,
     1
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     0,
     2
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     0,
     3
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     0,
     4
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     0,
     5
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     0,
     6
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     0,
     7
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     1,
     2
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     1,
     3
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     1,
     4
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     1,
     5
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     1,
     6
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     1,
     7
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     2,
     3
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     2,
     4
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     2,
     5
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     2,
     6
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     2,
     7
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     3,
     4
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     3,
     5
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     3,
     6
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     3,
     7
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     4,
     5
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     4,
     6
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     4,
     7
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     5,
     6
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     5,
     7
    ],
    "param": "crz_all"
   },
   {
    "gate": "CRZ",
    "wires": [
     6,
     7
    ],
    "param": "crz_all"
   },
   {
    "gate": "RZ",
    "wires": [
     0
    ],
    "param": "rz_all"
   },
   {
    "gate": "RZ",
    "wires": [
     1
    ],
    "param": "rz_all"
   },
   {
    "gate": "RZ",
    "wires": [
     2
    ],
    "param": "rz_all"
   },
   {
    "gate": "RZ",
    "wires": [
     3
    ],
    "param": "rz_all"
   },
   {
    "gate": "RZ",
    "wires": [
     4
    ],
    "param": "rz_all"
   },
   {
    "gate": "RZ",
    "wires": [
     5
    ],
    "param": "rz_all"
   },
   {
    "gate": "RZ",
    "wires": [
     6
    ],
    "param": "rz_all"
   },
   {
    "gate": "RZ",
    "wires": [
     7
    ],
    "param": "rz_all"
   }
  ],
  "stats": {
   "n_gates": 44,
   "n_params_per_block": 3,
   "n_params": 20,
   "families": [
    {
     "param": "crz_all",
     "gates": [
      "CRZ"
     ],
     "count": 28
    },
    {
     "param": "ry_all",
     "gates": [
      "RY"
     ],
     "count": 8
    },
    {
     "param": "rz_all",
     "gates": [
      "RZ"
     ],
     "count": 8
    }
   ]
  }
 },
 {
  "key": "weak-gen38",
  "kind": "best",
  "tier": "weak",
  "run": "results_or_weak_r1",
  "title": "weak ensemble \u2014 generation 38",
  "source": "experiments/transfer-sn/results_or_weak_r1/programs.sqlite",
  "program_id": "4e7870b9-3b45-48de-9f10-057e219d9ec5",
  "parent_id": "6cf1aaa5-662b-4b6a-a274-ebbf79b0fa91",
  "generation": 38,
  "score": 0.8344407576620463,
  "model_name": "openrouter/qwen/qwen3-coder",
  "patch_type": "diff",
  "patch_name": "learnable_entangling_strengths",
  "patch_description": "This change implements the recommendation to make all entanglers learnable via shared CRZ scales. The idea is to replace every CZ gate in ANSATZ_SPEC with CRZ gates, using two new per-block parameters \"chi_ring\" (for the eight ring edges) and \"chi_chord\" (for the four opposite-qubit chords). This adds 2 parameters per block (total N_PARAMS=38), retains the exact entanglement topology and corridor depth, and probes whether tuning entangling strengths can push raw scores above 0.91. This approach maintains the proven entanglement structure while adding flexibility to the entangling operations.",
  "metrics": {
   "test_accuracy_mean": 0.9517,
   "validation_accuracy_mean": 0.95,
   "generalization_gap_mean": 0.005,
   "validation_loss_mean": 0.298,
   "n_params": 50,
   "depth_mean": 105.0,
   "gate_count_mean": 300.0,
   "convergence_step_mean": 180.0
  },
  "gates": [
   {
    "gate": "RY",
    "wires": [
     0
    ],
    "param": "ry_h"
   },
   {
    "gate": "RY",
    "wires": [
     1
    ],
    "param": "ry_h"
   },
   {
    "gate": "RY",
    "wires": [
     2
    ],
    "param": "ry_h"
   },
   {
    "gate": "RY",
    "wires": [
     3
    ],
    "param": "ry_h"
   },
   {
    "gate": "RY",
    "wires": [
     4
    ],
    "param": "ry_h2"
   },
   {
    "gate": "RY",
    "wires": [
     5
    ],
    "param": "ry_h2"
   },
   {
    "gate": "RY",
    "wires": [
     6
    ],
    "param": "ry_h2"
   },
   {
    "gate": "RY",
    "wires": [
     7
    ],
    "param": "ry_h2"
   },
   {
    "gate": "RZ",
    "wires": [
     0
    ],
    "param": "rz_pre_h"
   },
   {
    "gate": "RZ",
    "wires": [
     1
    ],
    "param": "rz_pre_h"
   },
   {
    "gate": "RZ",
    "wires": [
     2
    ],
    "param": "rz_pre_h"
   },
   {
    "gate": "RZ",
    "wires": [
     3
    ],
    "param": "rz_pre_h"
   },
   {
    "gate": "RZ",
    "wires": [
     4
    ],
    "param": "rz_pre_h2"
   },
   {
    "gate": "RZ",
    "wires": [
     5
    ],
    "param": "rz_pre_h2"
   },
   {
    "gate": "RZ",
    "wires": [
     6
    ],
    "param": "rz_pre_h2"
   },
   {
    "gate": "RZ",
    "wires": [
     7
    ],
    "param": "rz_pre_h2"
   },
   {
    "gate": "CRZ",
    "wires": [
     0,
     2
    ],
    "param": "chi_ring"
   },
   {
    "gate": "CRZ",
    "wires": [
     2,
     4
    ],
    "param": "chi_ring"
   },
   {
    "gate": "CRZ",
    "wires": [
     4,
     6
    ],
    "param": "chi_ring"
   },
   {
    "gate": "CRZ",
    "wires": [
     6,
     0
    ],
    "param": "chi_ring"
   },
   {
    "gate": "CRZ",
    "wires": [
     1,
     3
    ],
    "param": "chi_ring"
   },
   {
    "gate": "CRZ",
    "wires": [
     3,
     5
    ],
    "param": "chi_ring"
   },
   {
    "gate": "CRZ",
    "wires": [
     5,
     7
    ],
    "param": "chi_ring"
   },
   {
    "gate": "CRZ",
    "wires": [
     7,
     1
    ],
    "param": "chi_ring"
   },
   {
    "gate": "CRZ",
    "wires": [
     0,
     4
    ],
    "param": "chi_chord"
   },
   {
    "gate": "CRZ",
    "wires": [
     1,
     5
    ],
    "param": "chi_chord"
   },
   {
    "gate": "CRZ",
    "wires": [
     2,
     6
    ],
    "param": "chi_chord"
   },
   {
    "gate": "CRZ",
    "wires": [
     3,
     7
    ],
    "param": "chi_chord"
   },
   {
    "gate": "RZ",
    "wires": [
     0
    ],
    "param": "rz_post_h"
   },
   {
    "gate": "RZ",
    "wires": [
     1
    ],
    "param": "rz_post_h"
   },
   {
    "gate": "RZ",
    "wires": [
     2
    ],
    "param": "rz_post_h"
   },
   {
    "gate": "RZ",
    "wires": [
     3
    ],
    "param": "rz_post_h"
   },
   {
    "gate": "RZ",
    "wires": [
     4
    ],
    "param": "rz_post_h2"
   },
   {
    "gate": "RZ",
    "wires": [
     5
    ],
    "param": "rz_post_h2"
   },
   {
    "gate": "RZ",
    "wires": [
     6
    ],
    "param": "rz_post_h2"
   },
   {
    "gate": "RZ",
    "wires": [
     7
    ],
    "param": "rz_post_h2"
   }
  ],
  "stats": {
   "n_gates": 36,
   "n_params_per_block": 8,
   "n_params": 50,
   "families": [
    {
     "param": "chi_ring",
     "gates": [
      "CRZ"
     ],
     "count": 8
    },
    {
     "param": "ry_h",
     "gates": [
      "RY"
     ],
     "count": 4
    },
    {
     "param": "ry_h2",
     "gates": [
      "RY"
     ],
     "count": 4
    },
    {
     "param": "rz_pre_h",
     "gates": [
      "RZ"
     ],
     "count": 4
    },
    {
     "param": "rz_pre_h2",
     "gates": [
      "RZ"
     ],
     "count": 4
    },
    {
     "param": "chi_chord",
     "gates": [
      "CRZ"
     ],
     "count": 4
    },
    {
     "param": "rz_post_h",
     "gates": [
      "RZ"
     ],
     "count": 4
    },
    {
     "param": "rz_post_h2",
     "gates": [
      "RZ"
     ],
     "count": 4
    }
   ]
  }
 },
 {
  "key": "mid-gen20",
  "kind": "best",
  "tier": "mid",
  "run": "results_or_mid_r1",
  "title": "mid ensemble \u2014 generation 20",
  "source": "experiments/transfer-sn/results_or_mid_r1/programs.sqlite",
  "program_id": "fa741557-e113-4491-8f3d-ffa0afffecdb",
  "parent_id": "8b977720-2f19-4121-8034-85fbf1920565",
  "generation": 20,
  "score": 0.27250520910961434,
  "model_name": "openrouter/openai/gpt-5.4-mini",
  "patch_type": "cross",
  "patch_name": "hybrid_mirror_cz_crmix",
  "patch_description": "This crossover ansatz keeps the efficient 12-parameter-per-block budget of the stronger shared-parameter design, while importing the broader candidate\u2019s idea of mixed controlled-rotation entanglers. The block uses:\n- mirrored shared RY pre-rotations for stable feature lifting,\n- a fixed CZ scaffold to add regularizing entanglement at zero parameter cost,\n- a small mixed-axis controlled-rotation core (CRX/CRY/CRZ) for expressive nonlinear mixing,\n- mirrored shared RZ post-rotations to refine readout-sensitive phases.\n\nThe result preserves the same training loop and I/O, but should reduce overfitting relative to the larger ansatz while retaining enough expressivity for fast convergence.",
  "metrics": {
   "test_accuracy_mean": 0.8667,
   "validation_accuracy_mean": 0.9133,
   "generalization_gap_mean": 0.0622,
   "validation_loss_mean": 0.3931,
   "n_params": 74,
   "depth_mean": 87.0,
   "gate_count_mean": 252.0,
   "convergence_step_mean": 270.0
  },
  "gates": [
   {
    "gate": "RY",
    "wires": [
     0
    ],
    "param": "ry_g0"
   },
   {
    "gate": "RY",
    "wires": [
     1
    ],
    "param": "ry_g0"
   },
   {
    "gate": "RY",
    "wires": [
     2
    ],
    "param": "ry_g1"
   },
   {
    "gate": "RY",
    "wires": [
     3
    ],
    "param": "ry_g1"
   },
   {
    "gate": "RY",
    "wires": [
     4
    ],
    "param": "ry_g2"
   },
   {
    "gate": "RY",
    "wires": [
     5
    ],
    "param": "ry_g2"
   },
   {
    "gate": "RY",
    "wires": [
     6
    ],
    "param": "ry_g3"
   },
   {
    "gate": "RY",
    "wires": [
     7
    ],
    "param": "ry_g3"
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     4
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     3,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     1
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     3
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     4,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     6,
     7
    ],
    "param": null
   },
   {
    "gate": "CRX",
    "wires": [
     0,
     7
    ],
    "param": "crx_a"
   },
   {
    "gate": "CRY",
    "wires": [
     1,
     6
    ],
    "param": "cry_a"
   },
   {
    "gate": "CRZ",
    "wires": [
     2,
     5
    ],
    "param": "crz_a"
   },
   {
    "gate": "CRY",
    "wires": [
     3,
     4
    ],
    "param": "cry_b"
   },
   {
    "gate": "RZ",
    "wires": [
     0
    ],
    "param": "rz_g0"
   },
   {
    "gate": "RZ",
    "wires": [
     7
    ],
    "param": "rz_g0"
   },
   {
    "gate": "RZ",
    "wires": [
     1
    ],
    "param": "rz_g1"
   },
   {
    "gate": "RZ",
    "wires": [
     6
    ],
    "param": "rz_g1"
   },
   {
    "gate": "RZ",
    "wires": [
     2
    ],
    "param": "rz_g2"
   },
   {
    "gate": "RZ",
    "wires": [
     5
    ],
    "param": "rz_g2"
   },
   {
    "gate": "RZ",
    "wires": [
     3
    ],
    "param": "rz_g3"
   },
   {
    "gate": "RZ",
    "wires": [
     4
    ],
    "param": "rz_g3"
   }
  ],
  "stats": {
   "n_gates": 28,
   "n_params_per_block": 12,
   "n_params": 74,
   "families": [
    {
     "param": "ry_g0",
     "gates": [
      "RY"
     ],
     "count": 2
    },
    {
     "param": "ry_g1",
     "gates": [
      "RY"
     ],
     "count": 2
    },
    {
     "param": "ry_g2",
     "gates": [
      "RY"
     ],
     "count": 2
    },
    {
     "param": "ry_g3",
     "gates": [
      "RY"
     ],
     "count": 2
    },
    {
     "param": "rz_g0",
     "gates": [
      "RZ"
     ],
     "count": 2
    },
    {
     "param": "rz_g1",
     "gates": [
      "RZ"
     ],
     "count": 2
    },
    {
     "param": "rz_g2",
     "gates": [
      "RZ"
     ],
     "count": 2
    },
    {
     "param": "rz_g3",
     "gates": [
      "RZ"
     ],
     "count": 2
    },
    {
     "param": "crx_a",
     "gates": [
      "CRX"
     ],
     "count": 1
    },
    {
     "param": "cry_a",
     "gates": [
      "CRY"
     ],
     "count": 1
    },
    {
     "param": "crz_a",
     "gates": [
      "CRZ"
     ],
     "count": 1
    },
    {
     "param": "cry_b",
     "gates": [
      "CRY"
     ],
     "count": 1
    }
   ]
  }
 },
 {
  "key": "frontier-gen0",
  "kind": "lineage",
  "tier": "frontier",
  "run": "results_or_frontier_r1",
  "title": "frontier ensemble \u2014 generation 0",
  "source": "experiments/transfer-sn/results_or_frontier_r1/programs.sqlite",
  "program_id": "52e0e020-0e58-42ac-aee4-13479c183aa5",
  "parent_id": null,
  "generation": 0,
  "score": 0.0,
  "model_name": null,
  "patch_type": "init",
  "patch_name": "initial_program",
  "patch_description": "Initial program setup",
  "metrics": {
   "test_accuracy_mean": 0.8667,
   "validation_accuracy_mean": 0.89,
   "generalization_gap_mean": 0.0711,
   "validation_loss_mean": 0.4561,
   "n_params": 146,
   "depth_mean": 99.0,
   "gate_count_mean": 270.0,
   "convergence_step_mean": 750.0
  },
  "gates": [
   {
    "gate": "RY",
    "wires": [
     0
    ],
    "param": "ry_0"
   },
   {
    "gate": "RY",
    "wires": [
     1
    ],
    "param": "ry_1"
   },
   {
    "gate": "RY",
    "wires": [
     2
    ],
    "param": "ry_2"
   },
   {
    "gate": "RY",
    "wires": [
     3
    ],
    "param": "ry_3"
   },
   {
    "gate": "RY",
    "wires": [
     4
    ],
    "param": "ry_4"
   },
   {
    "gate": "RY",
    "wires": [
     5
    ],
    "param": "ry_5"
   },
   {
    "gate": "RY",
    "wires": [
     6
    ],
    "param": "ry_6"
   },
   {
    "gate": "RY",
    "wires": [
     7
    ],
    "param": "ry_7"
   },
   {
    "gate": "RZ",
    "wires": [
     0
    ],
    "param": "rz_pre_0"
   },
   {
    "gate": "RZ",
    "wires": [
     1
    ],
    "param": "rz_pre_1"
   },
   {
    "gate": "RZ",
    "wires": [
     2
    ],
    "param": "rz_pre_2"
   },
   {
    "gate": "RZ",
    "wires": [
     3
    ],
    "param": "rz_pre_3"
   },
   {
    "gate": "RZ",
    "wires": [
     4
    ],
    "param": "rz_pre_4"
   },
   {
    "gate": "RZ",
    "wires": [
     5
    ],
    "param": "rz_pre_5"
   },
   {
    "gate": "RZ",
    "wires": [
     6
    ],
    "param": "rz_pre_6"
   },
   {
    "gate": "RZ",
    "wires": [
     7
    ],
    "param": "rz_pre_7"
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     1
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     2
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     3
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     3,
     4
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     4,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     5,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     6,
     7
    ],
    "param": null
   },
   {
    "gate": "RZ",
    "wires": [
     0
    ],
    "param": "rz_post_0"
   },
   {
    "gate": "RZ",
    "wires": [
     1
    ],
    "param": "rz_post_1"
   },
   {
    "gate": "RZ",
    "wires": [
     2
    ],
    "param": "rz_post_2"
   },
   {
    "gate": "RZ",
    "wires": [
     3
    ],
    "param": "rz_post_3"
   },
   {
    "gate": "RZ",
    "wires": [
     4
    ],
    "param": "rz_post_4"
   },
   {
    "gate": "RZ",
    "wires": [
     5
    ],
    "param": "rz_post_5"
   },
   {
    "gate": "RZ",
    "wires": [
     6
    ],
    "param": "rz_post_6"
   },
   {
    "gate": "RZ",
    "wires": [
     7
    ],
    "param": "rz_post_7"
   }
  ],
  "stats": {
   "n_gates": 31,
   "n_params_per_block": 24,
   "n_params": 146,
   "families": [
    {
     "param": "ry_0",
     "gates": [
      "RY"
     ],
     "count": 1
    },
    {
     "param": "ry_1",
     "gates": [
      "RY"
     ],
     "count": 1
    },
    {
     "param": "ry_2",
     "gates": [
      "RY"
     ],
     "count": 1
    },
    {
     "param": "ry_3",
     "gates": [
      "RY"
     ],
     "count": 1
    },
    {
     "param": "ry_4",
     "gates": [
      "RY"
     ],
     "count": 1
    },
    {
     "param": "ry_5",
     "gates": [
      "RY"
     ],
     "count": 1
    },
    {
     "param": "ry_6",
     "gates": [
      "RY"
     ],
     "count": 1
    },
    {
     "param": "ry_7",
     "gates": [
      "RY"
     ],
     "count": 1
    },
    {
     "param": "rz_pre_0",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_pre_1",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_pre_2",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_pre_3",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_pre_4",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_pre_5",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_pre_6",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_pre_7",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_post_0",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_post_1",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_post_2",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_post_3",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_post_4",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_post_5",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_post_6",
     "gates": [
      "RZ"
     ],
     "count": 1
    },
    {
     "param": "rz_post_7",
     "gates": [
      "RZ"
     ],
     "count": 1
    }
   ]
  }
 },
 {
  "key": "frontier-gen5",
  "kind": "lineage",
  "tier": "frontier",
  "run": "results_or_frontier_r1",
  "title": "frontier ensemble \u2014 generation 5",
  "source": "experiments/transfer-sn/results_or_frontier_r1/programs.sqlite",
  "program_id": "ece121c4-4aee-4d48-8e26-783e14614edb",
  "parent_id": "52e0e020-0e58-42ac-aee4-13479c183aa5",
  "generation": 5,
  "score": 0.7840443598490842,
  "model_name": "openrouter/openai/gpt-5.6-sol",
  "patch_type": "diff",
  "patch_name": "symmetric_graph_mixer",
  "patch_description": "Replace the wire-specific line ansatz with a permutation-equivariant, QAOA-inspired graph mixer. Each rotation angle is shared across all eight qubits, while a commuting complete-graph CZ layer supplies symmetric nonlinear entanglement without privileging an arbitrary vertex ordering. The final RX layer converts phases created by the feature-map, CZ, and RZ operations into measurable Z populations; unlike the seed's terminal RZ layer, it directly affects the readout. This reduces the circuit parameters from 146 to 20, should reduce overfitting and the train-test gap, and lets Adam aggregate gradients across all qubits for faster optimization.",
  "metrics": {
   "test_accuracy_mean": 0.9417,
   "validation_accuracy_mean": 0.95,
   "generalization_gap_mean": 0.0183,
   "validation_loss_mean": 0.3024,
   "n_params": 20,
   "depth_mean": 135.0,
   "gate_count_mean": 396.0,
   "convergence_step_mean": 150.0
  },
  "gates": [
   {
    "gate": "RY",
    "wires": [
     0
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     1
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     2
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     3
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     4
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     5
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     6
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     7
    ],
    "param": "collective_ry"
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     1
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     2
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     3
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     4
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     2
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     3
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     4
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     3
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     4
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     3,
     4
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     3,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     3,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     3,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     4,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     4,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     4,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     5,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     5,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     6,
     7
    ],
    "param": null
   },
   {
    "gate": "RZ",
    "wires": [
     0
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     1
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     2
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     3
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     4
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     5
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     6
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     7
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RX",
    "wires": [
     0
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     1
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     2
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     3
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     4
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     5
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     6
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     7
    ],
    "param": "collective_rx"
   }
  ],
  "stats": {
   "n_gates": 52,
   "n_params_per_block": 3,
   "n_params": 20,
   "families": [
    {
     "param": "collective_ry",
     "gates": [
      "RY"
     ],
     "count": 8
    },
    {
     "param": "collective_rz",
     "gates": [
      "RZ"
     ],
     "count": 8
    },
    {
     "param": "collective_rx",
     "gates": [
      "RX"
     ],
     "count": 8
    }
   ]
  }
 },
 {
  "key": "frontier-gen10",
  "kind": "lineage",
  "tier": "frontier",
  "run": "results_or_frontier_r1",
  "title": "frontier ensemble \u2014 generation 10",
  "source": "experiments/transfer-sn/results_or_frontier_r1/programs.sqlite",
  "program_id": "5fddbc19-5960-4866-bd7b-f6013aa227fa",
  "parent_id": "ece121c4-4aee-4d48-8e26-783e14614edb",
  "generation": 10,
  "score": 0.7840443598490842,
  "model_name": "openrouter/openai/gpt-5.6-sol",
  "patch_type": "full",
  "patch_name": "scheduled_complete_graph",
  "patch_description": "Reorders the complete-graph CZ entangler into seven disjoint perfect matchings. Because all CZ gates commute, this preserves the current model\u2019s unitary, parameter count, training behavior, and strong accuracy while substantially reducing entangling depth. The ansatz retains only three shared parameters per block and 20 total parameters.",
  "metrics": {
   "test_accuracy_mean": 0.9417,
   "validation_accuracy_mean": 0.95,
   "generalization_gap_mean": 0.0183,
   "validation_loss_mean": 0.3024,
   "n_params": 20,
   "depth_mean": 117.0,
   "gate_count_mean": 396.0,
   "convergence_step_mean": 150.0
  },
  "gates": [
   {
    "gate": "RY",
    "wires": [
     0
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     1
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     2
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     3
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     4
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     5
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     6
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     7
    ],
    "param": "collective_ry"
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     1
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     3
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     4,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     6,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     2
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     3
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     4,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     5,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     4
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     3,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     3
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     2
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     4,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     5,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     3,
     4
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     4
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     3,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     4
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     3,
     6
    ],
    "param": null
   },
   {
    "gate": "RZ",
    "wires": [
     0
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     1
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     2
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     3
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     4
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     5
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     6
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     7
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RX",
    "wires": [
     0
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     1
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     2
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     3
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     4
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     5
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     6
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     7
    ],
    "param": "collective_rx"
   }
  ],
  "stats": {
   "n_gates": 52,
   "n_params_per_block": 3,
   "n_params": 20,
   "families": [
    {
     "param": "collective_ry",
     "gates": [
      "RY"
     ],
     "count": 8
    },
    {
     "param": "collective_rz",
     "gates": [
      "RZ"
     ],
     "count": 8
    },
    {
     "param": "collective_rx",
     "gates": [
      "RX"
     ],
     "count": 8
    }
   ]
  }
 },
 {
  "key": "frontier-gen28",
  "kind": "lineage",
  "tier": "frontier",
  "run": "results_or_frontier_r1",
  "title": "frontier ensemble \u2014 generation 28",
  "source": "experiments/transfer-sn/results_or_frontier_r1/programs.sqlite",
  "program_id": "20cb8330-c479-4295-86d5-fd188b853104",
  "parent_id": "5fddbc19-5960-4866-bd7b-f6013aa227fa",
  "generation": 28,
  "score": 1.0686688274229394,
  "model_name": "openrouter/openai/gpt-5.6-sol",
  "patch_type": "diff",
  "patch_name": "two_axis_midpoint_mixer",
  "patch_description": "Restore the proven collective RX input axis, then insert one independently trainable collective RY/RX mixer after the fourth perfect matching. In the current block, all CZ gates commute and effectively form one diagonal K8 layer; the midpoint non-diagonal mixer separates that layer into two interacting stages so partial correlations can be transformed before the remaining entanglers. Sharing each angle across all qubits preserves parameter efficiency and regularization. The midpoint parameters are independent, so setting them to zero recovers the strong prior two-axis architecture as a subspace. This adds only three parameter keys per block, resulting in 38 total parameters while targeting faster convergence and lower validation loss.",
  "metrics": {
   "test_accuracy_mean": 0.97,
   "validation_accuracy_mean": 0.98,
   "generalization_gap_mean": 0.0056,
   "validation_loss_mean": 0.2519,
   "n_params": 38,
   "depth_mean": 135.0,
   "gate_count_mean": 540.0,
   "convergence_step_mean": 150.0
  },
  "gates": [
   {
    "gate": "RY",
    "wires": [
     0
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     1
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     2
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     3
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     4
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     5
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     6
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     7
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RX",
    "wires": [
     0
    ],
    "param": "collective_rx_in"
   },
   {
    "gate": "RX",
    "wires": [
     1
    ],
    "param": "collective_rx_in"
   },
   {
    "gate": "RX",
    "wires": [
     2
    ],
    "param": "collective_rx_in"
   },
   {
    "gate": "RX",
    "wires": [
     3
    ],
    "param": "collective_rx_in"
   },
   {
    "gate": "RX",
    "wires": [
     4
    ],
    "param": "collective_rx_in"
   },
   {
    "gate": "RX",
    "wires": [
     5
    ],
    "param": "collective_rx_in"
   },
   {
    "gate": "RX",
    "wires": [
     6
    ],
    "param": "collective_rx_in"
   },
   {
    "gate": "RX",
    "wires": [
     7
    ],
    "param": "collective_rx_in"
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     1
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     3
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     4,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     6,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     2
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     3
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     4,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     5,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     4
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     3,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     3
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     2
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     4,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     5,
     6
    ],
    "param": null
   },
   {
    "gate": "RY",
    "wires": [
     0
    ],
    "param": "collective_ry_mid"
   },
   {
    "gate": "RY",
    "wires": [
     1
    ],
    "param": "collective_ry_mid"
   },
   {
    "gate": "RY",
    "wires": [
     2
    ],
    "param": "collective_ry_mid"
   },
   {
    "gate": "RY",
    "wires": [
     3
    ],
    "param": "collective_ry_mid"
   },
   {
    "gate": "RY",
    "wires": [
     4
    ],
    "param": "collective_ry_mid"
   },
   {
    "gate": "RY",
    "wires": [
     5
    ],
    "param": "collective_ry_mid"
   },
   {
    "gate": "RY",
    "wires": [
     6
    ],
    "param": "collective_ry_mid"
   },
   {
    "gate": "RY",
    "wires": [
     7
    ],
    "param": "collective_ry_mid"
   },
   {
    "gate": "RX",
    "wires": [
     0
    ],
    "param": "collective_rx_mid"
   },
   {
    "gate": "RX",
    "wires": [
     1
    ],
    "param": "collective_rx_mid"
   },
   {
    "gate": "RX",
    "wires": [
     2
    ],
    "param": "collective_rx_mid"
   },
   {
    "gate": "RX",
    "wires": [
     3
    ],
    "param": "collective_rx_mid"
   },
   {
    "gate": "RX",
    "wires": [
     4
    ],
    "param": "collective_rx_mid"
   },
   {
    "gate": "RX",
    "wires": [
     5
    ],
    "param": "collective_rx_mid"
   },
   {
    "gate": "RX",
    "wires": [
     6
    ],
    "param": "collective_rx_mid"
   },
   {
    "gate": "RX",
    "wires": [
     7
    ],
    "param": "collective_rx_mid"
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     3,
     4
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     4
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     3,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     4
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     3,
     6
    ],
    "param": null
   },
   {
    "gate": "RZ",
    "wires": [
     0
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     1
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     2
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     3
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     4
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     5
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     6
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     7
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RX",
    "wires": [
     0
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     1
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     2
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     3
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     4
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     5
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     6
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     7
    ],
    "param": "collective_rx"
   }
  ],
  "stats": {
   "n_gates": 76,
   "n_params_per_block": 6,
   "n_params": 38,
   "families": [
    {
     "param": "collective_ry",
     "gates": [
      "RY"
     ],
     "count": 8
    },
    {
     "param": "collective_rx_in",
     "gates": [
      "RX"
     ],
     "count": 8
    },
    {
     "param": "collective_ry_mid",
     "gates": [
      "RY"
     ],
     "count": 8
    },
    {
     "param": "collective_rx_mid",
     "gates": [
      "RX"
     ],
     "count": 8
    },
    {
     "param": "collective_rz",
     "gates": [
      "RZ"
     ],
     "count": 8
    },
    {
     "param": "collective_rx",
     "gates": [
      "RX"
     ],
     "count": 8
    }
   ]
  }
 },
 {
  "key": "frontier-gen39",
  "kind": "lineage-best",
  "tier": "frontier",
  "run": "results_or_frontier_r1",
  "title": "frontier ensemble \u2014 generation 39",
  "source": "experiments/transfer-sn/results_or_frontier_r1/programs.sqlite",
  "program_id": "b90573df-f58c-4435-ba6c-699ca8bda62f",
  "parent_id": "20cb8330-c479-4295-86d5-fd188b853104",
  "generation": 39,
  "score": 1.1001686256240462,
  "model_name": "openrouter/openai/gpt-5.6-sol",
  "patch_type": "cross",
  "patch_name": "shared_midpoint_crossover",
  "patch_description": "This crossover retains the current program\u2019s accuracy-improving split complete-graph entangler and two-axis midpoint mixer, while reducing the midpoint from two independent parameters to one shared `collective_mid` parameter. The resulting block has five parameters instead of six, reducing the full model from 38 to 32 parameters. Setting the midpoint parameter to zero recovers the efficient parent topology, while nonzero values provide the noncommuting interaction stages associated with the stronger current result. Parameter sharing across all wires preserves permutation symmetry, aggregates gradients, and acts as regularization.",
  "metrics": {
   "test_accuracy_mean": 0.985,
   "validation_accuracy_mean": 0.9767,
   "generalization_gap_mean": 0.0028,
   "validation_loss_mean": 0.2217,
   "n_params": 32,
   "depth_mean": 135.0,
   "gate_count_mean": 540.0,
   "convergence_step_mean": 270.0
  },
  "gates": [
   {
    "gate": "RY",
    "wires": [
     0
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     1
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     2
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     3
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     4
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     5
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     6
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RY",
    "wires": [
     7
    ],
    "param": "collective_ry"
   },
   {
    "gate": "RX",
    "wires": [
     0
    ],
    "param": "collective_rx_in"
   },
   {
    "gate": "RX",
    "wires": [
     1
    ],
    "param": "collective_rx_in"
   },
   {
    "gate": "RX",
    "wires": [
     2
    ],
    "param": "collective_rx_in"
   },
   {
    "gate": "RX",
    "wires": [
     3
    ],
    "param": "collective_rx_in"
   },
   {
    "gate": "RX",
    "wires": [
     4
    ],
    "param": "collective_rx_in"
   },
   {
    "gate": "RX",
    "wires": [
     5
    ],
    "param": "collective_rx_in"
   },
   {
    "gate": "RX",
    "wires": [
     6
    ],
    "param": "collective_rx_in"
   },
   {
    "gate": "RX",
    "wires": [
     7
    ],
    "param": "collective_rx_in"
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     1
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     3
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     4,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     6,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     2
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     3
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     4,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     5,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     4
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     3,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     3
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     2
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     4,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     5,
     6
    ],
    "param": null
   },
   {
    "gate": "RY",
    "wires": [
     0
    ],
    "param": "collective_mid"
   },
   {
    "gate": "RY",
    "wires": [
     1
    ],
    "param": "collective_mid"
   },
   {
    "gate": "RY",
    "wires": [
     2
    ],
    "param": "collective_mid"
   },
   {
    "gate": "RY",
    "wires": [
     3
    ],
    "param": "collective_mid"
   },
   {
    "gate": "RY",
    "wires": [
     4
    ],
    "param": "collective_mid"
   },
   {
    "gate": "RY",
    "wires": [
     5
    ],
    "param": "collective_mid"
   },
   {
    "gate": "RY",
    "wires": [
     6
    ],
    "param": "collective_mid"
   },
   {
    "gate": "RY",
    "wires": [
     7
    ],
    "param": "collective_mid"
   },
   {
    "gate": "RX",
    "wires": [
     0
    ],
    "param": "collective_mid"
   },
   {
    "gate": "RX",
    "wires": [
     1
    ],
    "param": "collective_mid"
   },
   {
    "gate": "RX",
    "wires": [
     2
    ],
    "param": "collective_mid"
   },
   {
    "gate": "RX",
    "wires": [
     3
    ],
    "param": "collective_mid"
   },
   {
    "gate": "RX",
    "wires": [
     4
    ],
    "param": "collective_mid"
   },
   {
    "gate": "RX",
    "wires": [
     5
    ],
    "param": "collective_mid"
   },
   {
    "gate": "RX",
    "wires": [
     6
    ],
    "param": "collective_mid"
   },
   {
    "gate": "RX",
    "wires": [
     7
    ],
    "param": "collective_mid"
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     3,
     4
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     6
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     4
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     3,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     0,
     7
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     1,
     4
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     2,
     5
    ],
    "param": null
   },
   {
    "gate": "CZ",
    "wires": [
     3,
     6
    ],
    "param": null
   },
   {
    "gate": "RZ",
    "wires": [
     0
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     1
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     2
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     3
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     4
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     5
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     6
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RZ",
    "wires": [
     7
    ],
    "param": "collective_rz"
   },
   {
    "gate": "RX",
    "wires": [
     0
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     1
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     2
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     3
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     4
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     5
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     6
    ],
    "param": "collective_rx"
   },
   {
    "gate": "RX",
    "wires": [
     7
    ],
    "param": "collective_rx"
   }
  ],
  "stats": {
   "n_gates": 76,
   "n_params_per_block": 5,
   "n_params": 32,
   "families": [
    {
     "param": "collective_mid",
     "gates": [
      "RY",
      "RX"
     ],
     "count": 16
    },
    {
     "param": "collective_ry",
     "gates": [
      "RY"
     ],
     "count": 8
    },
    {
     "param": "collective_rx_in",
     "gates": [
      "RX"
     ],
     "count": 8
    },
    {
     "param": "collective_rz",
     "gates": [
      "RZ"
     ],
     "count": 8
    },
    {
     "param": "collective_rx",
     "gates": [
      "RX"
     ],
     "count": 8
    }
   ]
  }
 }
];
