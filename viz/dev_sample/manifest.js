window.VIZ_MANIFEST = {
  "generated_at": "2026-08-04T12:00:00Z",
  "runs": [
    {
      "id": "sample",
      "task": "tic-tac-toe",
      "variant": "islands2_seed42",
      "model": "claude-sonnet-4-5 + claude-opus-4-1",
      "label": "Dev sample: 2-island run with a gen-33 phase transition",
      "db_path": "/fake/path/does/not/exist/sample.db",
      "n_programs": 41,
      "max_generation": 40,
      "best_score": 0.9436,
      "best_program_id": "p0028"
    },
    {
      "id": "sample_missing",
      "task": "tic-tac-toe",
      "variant": "islands1_control",
      "model": "claude-sonnet-4-5",
      "label": "Dev sample: intentionally missing run file (tests onerror path)",
      "db_path": "/fake/path/does/not/exist/missing.db",
      "n_programs": 0,
      "max_generation": 0,
      "best_score": 0.0,
      "best_program_id": null
    }
  ]
};
