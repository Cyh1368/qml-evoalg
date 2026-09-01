#!/usr/bin/env python3
"""Rewind results_or_frontier_r1 to generation 3 (gpt-5.6-sol's shared_cube_mixer,
score 0.4477) and continue for 5 more generations under a DIFFERENT ensemble.

25 runs: weak x10, mid x10, frontier x5, all with distinct UCB1 seeds.
Target num_generations = 8 (3 kept + 5 new). Structure copied verbatim from
setup_phase23.py, which was verified on 2026-08-13.

Run ON the Bouchet login node from ~/project/transfer_sn.
"""
import json, os, shutil, sqlite3, sys

TASKDIR = os.path.expanduser("~/project/transfer_sn")
os.chdir(TASKDIR)

SRC = "results_or_frontier_r1"
K = 3
TAG = "frw3"
ARMS = [("weak", 10, 5.0, 300), ("mid", 10, 8.0, 320), ("frontier", 5, 20.0, 340)]


def make_config(base_path, out_path, seed, gens, cap):
    cfg = json.load(open(base_path))
    cfg["evo"]["llm_dynamic_selection_kwargs"]["seed"] = seed
    cfg["evo"]["num_generations"] = gens
    cfg["evo"]["max_api_costs"] = cap
    with open(out_path, "w") as f:
        json.dump(cfg, f, indent=2)


def rewind_copy(src_dir, dst_dir, k):
    if os.path.exists(dst_dir):
        print(f"refusing to overwrite {dst_dir}", file=sys.stderr); sys.exit(1)
    os.makedirs(dst_dir)
    shutil.copy2(f"{src_dir}/programs.sqlite", f"{dst_dir}/programs.sqlite")
    for name in os.listdir(src_dir):
        if name.startswith("gen_") and int(name.split("_")[1]) <= k:
            shutil.copytree(f"{src_dir}/{name}", f"{dst_dir}/{name}")
    # no bandit_state.pkl: fresh bandit, and the roster changed anyway
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


if not os.path.isdir(SRC):
    print(f"missing {SRC}", file=sys.stderr); sys.exit(1)
if not os.access(os.path.expanduser("~/.openrouter_key"), os.R_OK):
    print("missing ~/.openrouter_key", file=sys.stderr); sys.exit(1)

jobs = []
for arm, reps, cap, seed0 in ARMS:
    base = f"shinka_config_or_{arm}_r1.json"
    if not os.path.exists(base):
        print(f"missing {base}", file=sys.stderr); sys.exit(1)
    for r in range(1, reps + 1):
        cfg = f"shinka_config_{TAG}_{arm}_r{r}.json"
        res = f"results_{TAG}_{arm}_r{r}"
        make_config(base, cfg, seed=seed0 + r, gens=K + 5, cap=cap)
        rewind_copy(SRC, res, K)
        jobs.append((cfg, res, f"{TAG}_{arm}_r{r}"))

with open(f"{TAG}_jobs.txt", "w") as f:
    for cfg, res, name in jobs:
        f.write(f"{name}\t{cfg}\t{res}\n")
print(f"\n{len(jobs)} runs prepared; job list in {TAG}_jobs.txt")
