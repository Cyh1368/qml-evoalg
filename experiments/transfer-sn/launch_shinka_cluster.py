#!/usr/bin/env python
"""Launch ShinkaEvolve on Bouchet with SLURM (slurm_conda) evaluation jobs.

The stock ``shinka.cli.run`` hardcodes ``job_type="local"`` + ``LocalJobConfig``,
so it can only run evals on the orchestrator node.  Here we drive
``ShinkaEvolveRunner`` directly with ``job_type="slurm_conda"`` so the orchestrator
(this process, on a login node — it needs OpenRouter internet) submits each
candidate evaluation as its own SLURM job on the CPU ``day`` partition.

The eval protocol is the CORRECTED converged one (full data + validation-loss
early stopping + restore-best-weights), enforced by the env exported in
``activate_eval_cluster.sh`` and honored by the seed program's training loop.

Run (from the task dir, on a login node):
    nohup python launch_shinka_cluster.py --generations 100 > orchestrator.log 2>&1 &
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, fields
from pathlib import Path

from shinka.core import EvolutionConfig, ShinkaEvolveRunner
from shinka.database import DatabaseConfig
from shinka.launch import SlurmCondaJobConfig

HERE = Path(__file__).resolve().parent


def _filter(d: dict, cls) -> dict:
    allowed = {f.name for f in fields(cls)}
    return {k: v for k, v in d.items() if k in allowed}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--generations", type=int, default=100)
    ap.add_argument("--config", default=str(HERE / "shinka_config.json"))
    ap.add_argument("--task-dir", default=str(HERE))
    ap.add_argument("--results-dir", default=str(HERE / "results"))
    ap.add_argument("--max-eval-jobs", type=int, default=8,
                    help="concurrent SLURM eval jobs in flight")
    ap.add_argument("--max-proposal-jobs", type=int, default=4)
    ap.add_argument("--max-db-workers", type=int, default=2)
    ap.add_argument("--partition", default="day")
    ap.add_argument("--time", default="06:00:00", help="per-eval SLURM walltime cap")
    ap.add_argument("--cpus", type=int, default=8)
    ap.add_argument("--mem", default="12G")
    args = ap.parse_args()

    task_dir = Path(args.task_dir).resolve()
    results_dir = Path(args.results_dir).resolve()
    results_dir.mkdir(parents=True, exist_ok=True)

    cfg = json.loads(Path(args.config).read_text())
    evo_in = dict(cfg.get("evo", {}))
    db_in = dict(cfg.get("db", {}))

    init_path = task_dir / "initial_program.py"
    evaluate_path = task_dir / "evaluate.py"
    init_str = init_path.read_text(encoding="utf-8")
    evaluate_str = evaluate_path.read_text(encoding="utf-8")

    evo_values = _filter(evo_in, EvolutionConfig)
    evo_values.update(
        num_generations=args.generations,
        job_type="slurm_conda",
        language="python",
        init_program_path=str(init_path),
        results_dir=str(results_dir),
    )
    evo_config = EvolutionConfig(**evo_values)
    db_config = DatabaseConfig(**_filter(db_in, DatabaseConfig))

    job_config = SlurmCondaJobConfig(
        eval_program_path=str(evaluate_path),
        activate_script=str(task_dir / "activate_eval_cluster.sh"),
        modules=["miniconda"],
        partition=args.partition,
        time=args.time,
        cpus=args.cpus,
        gpus=0,          # CPU-only; --gres=gpu:0 is accepted on the day partition
        mem=args.mem,
    )

    print("=== ShinkaEvolve cluster launch ===", flush=True)
    print("generations:", args.generations, flush=True)
    print("llm_models:", evo_values.get("llm_models"), flush=True)
    print("max_api_costs:", evo_values.get("max_api_costs"), flush=True)
    print("eval: slurm_conda partition=%s time=%s cpus=%d gpus=0 mem=%s"
          % (args.partition, args.time, args.cpus, args.mem), flush=True)
    print("max_eval_jobs:", args.max_eval_jobs, "results_dir:", results_dir, flush=True)

    runner = ShinkaEvolveRunner(
        evo_config=evo_config,
        job_config=job_config,
        db_config=db_config,
        init_program_str=init_str,
        evaluate_str=evaluate_str,
        max_evaluation_jobs=args.max_eval_jobs,
        max_proposal_jobs=args.max_proposal_jobs,
        max_db_workers=args.max_db_workers,
        verbose=True,
    )
    runner.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
