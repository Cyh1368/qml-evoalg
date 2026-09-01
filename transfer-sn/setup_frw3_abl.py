#!/usr/bin/env python3
"""Ablation companion to setup_frw3.py: 5 frontier runs continuing from gen 3 of
results_or_frontier_r1 with gpt-5.6-sol (which proposed shared_cube_mixer at that
generation) REMOVED from the roster. Tests whether opus-4.6 + gemini-3.1-pro can
carry the discovery forward on their own.

Run ON the Bouchet login node from ~/project/transfer_sn.
"""
import os, sys

import json, shutil, sqlite3

SRC, K = "results_or_frontier_r1", 3


def rewind_copy(src_dir, dst_dir, k):
    """Verbatim copy of setup_frw3.rewind_copy (imported would re-run that script)."""
    if os.path.exists(dst_dir):
        print(f"refusing to overwrite {dst_dir}", file=sys.stderr); sys.exit(1)
    os.makedirs(dst_dir)
    shutil.copy2(f"{src_dir}/programs.sqlite", f"{dst_dir}/programs.sqlite")
    for name in os.listdir(src_dir):
        if name.startswith("gen_") and int(name.split("_")[1]) <= k:
            shutil.copytree(f"{src_dir}/{name}", f"{dst_dir}/{name}")
    con = sqlite3.connect(f"{dst_dir}/programs.sqlite")
    cur = con.cursor()
    cur.execute("DELETE FROM programs WHERE generation > ?", (k,))
    cur.execute("DELETE FROM archive WHERE program_id NOT IN (SELECT id FROM programs)")
    cur.execute("DELETE FROM generation_event_log WHERE generation > ?", (k,))
    cur.execute("DELETE FROM attempt_log WHERE generation > ?", (k,))
    cur.execute("UPDATE programs SET children_count = "
                "(SELECT COUNT(*) FROM programs c WHERE c.parent_id = programs.id)")
    best = cur.execute(
        "SELECT id, combined_score, generation FROM programs "
        "WHERE correct = 1 ORDER BY combined_score DESC LIMIT 1").fetchone()
    assert best[2] == k, f"best is @gen{best[2]}, expected the gen-{k} program"
    for key, val in [("last_iteration", str(k)),
                     ("best_program_id", best[0]),
                     ("best_score_ever", str(best[1])),
                     ("best_score_generation", str(best[2]))]:
        cur.execute("UPDATE metadata_store SET value=? WHERE key=?", (val, key))
    con.commit()
    n, mx = cur.execute("SELECT COUNT(*), MAX(generation) FROM programs").fetchone()
    con.close()
    print(f"{dst_dir}: {n} programs, max gen {mx}, best {best[1]:.4f} @gen{best[2]}")

TASKDIR = os.path.expanduser("~/project/transfer_sn")
os.chdir(TASKDIR)

SOL = "openrouter/openai/gpt-5.6-sol"
TAG = "frw3_frontabl"
CAP = 20.0
SEED0 = 360

jobs = []
for r in range(1, 6):
    cfg_path = f"shinka_config_{TAG}_r{r}.json"
    res = f"results_{TAG}_r{r}"
    cfg = json.load(open("shinka_config_or_frontier_r1.json"))
    models = cfg["evo"]["llm_models"]
    assert SOL in models, models
    cfg["evo"]["llm_models"] = [m for m in models if m != SOL]
    cfg["evo"]["llm_dynamic_selection_kwargs"]["seed"] = SEED0 + r
    cfg["evo"]["num_generations"] = K + 5
    cfg["evo"]["max_api_costs"] = CAP
    json.dump(cfg, open(cfg_path, "w"), indent=2)
    rewind_copy(SRC, res, K)
    jobs.append((cfg_path, res, f"{TAG}_r{r}"))

print("roster:", json.load(open(f"shinka_config_{TAG}_r1.json"))["evo"]["llm_models"])
with open(f"{TAG}_jobs.txt", "w") as f:
    for cfg, res, name in jobs:
        f.write(f"{name}\t{cfg}\t{res}\n")
print(f"\n{len(jobs)} runs prepared; job list in {TAG}_jobs.txt")
