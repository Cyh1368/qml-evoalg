#!/usr/bin/env bash
# Drive the Bouchet run over an already-authenticated multiplexed SSH socket.
# Prereq: ssh_config_snippet added to ~/.ssh/config AND one interactive
#   `ssh bouchet`  (Duo completed) so the ControlMaster socket is live.
#
# Usage:
#   bash deploy_and_run.sh setup     # build the conda env on Bouchet (once)
#   bash deploy_and_run.sh submit    # stage code + submit the 25-task array
#   bash deploy_and_run.sh status    # squeue for the array
#   bash deploy_and_run.sh fetch     # rsync histories/ back, then plot locally
set -euo pipefail

HOST=bouchet
REMOTE_DIR='~/project/cemoid_sweep'          # ~ expands on the remote
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)" # paper-replication/

case "${1:-}" in
  setup)
    ssh "$HOST" "mkdir -p $REMOTE_DIR"
    rsync -av "$LOCAL_DIR/cluster/setup_env.sh" "$HOST:$REMOTE_DIR/"
    ssh "$HOST" "cd $REMOTE_DIR && bash setup_env.sh"
    ;;
  submit)
    ssh "$HOST" "mkdir -p $REMOTE_DIR/slurm_logs $REMOTE_DIR/histories"
    rsync -av "$LOCAL_DIR/sweep.py" "$LOCAL_DIR/../initial_program.py" \
              "$LOCAL_DIR/cluster/sweep_array.sbatch" "$HOST:$REMOTE_DIR/"
    ssh "$HOST" "cd $REMOTE_DIR && sbatch sweep_array.sbatch"
    ;;
  status)
    ssh "$HOST" "squeue --me; echo '--- finished histories ---'; ls $REMOTE_DIR/histories 2>/dev/null | wc -l"
    ;;
  fetch)
    rsync -av "$HOST:$REMOTE_DIR/histories/" "$LOCAL_DIR/histories/"
    ( cd "$LOCAL_DIR" && ../.venv-shinka-ttt/bin/python sweep.py --plot-only )
    ;;
  sweep-ext-submit)
    ssh "$HOST" "mkdir -p $REMOTE_DIR/slurm_logs $REMOTE_DIR/histories"
    rsync -av "$LOCAL_DIR/sweep.py" "$LOCAL_DIR/../initial_program.py" \
              "$LOCAL_DIR/cluster/sweep_ext_array.sbatch" "$HOST:$REMOTE_DIR/"
    ssh "$HOST" "cd $REMOTE_DIR && sbatch sweep_ext_array.sbatch"
    ;;
  sweep-ext-status)
    ssh "$HOST" "squeue --me; echo '--- finished histories (incl. 7x7) ---'; ls $REMOTE_DIR/histories 2>/dev/null | wc -l"
    ;;
  sweep-ext-fetch)
    rsync -av "$HOST:$REMOTE_DIR/histories/" "$LOCAL_DIR/histories/"
    echo "Fetched. Histories now: $(ls "$LOCAL_DIR/histories" | wc -l)"
    ;;
  robustness-submit)
    ssh "$HOST" "mkdir -p $REMOTE_DIR/slurm_logs $REMOTE_DIR/robustness_histories"
    rsync -av "$LOCAL_DIR/sweep.py" "$LOCAL_DIR/seed_robustness.py" \
              "$LOCAL_DIR/../initial_program.py" \
              "$LOCAL_DIR/cluster/robustness_array.sbatch" "$HOST:$REMOTE_DIR/"
    ssh "$HOST" "cd $REMOTE_DIR && sbatch robustness_array.sbatch"
    ;;
  robustness-status)
    ssh "$HOST" "squeue --me; echo '--- finished seeds ---'; ls $REMOTE_DIR/robustness_histories 2>/dev/null | wc -l"
    ;;
  robustness-fetch)
    rsync -av "$HOST:$REMOTE_DIR/robustness_histories/" "$LOCAL_DIR/robustness_histories/"
    ( cd "$LOCAL_DIR" && ../.venv-shinka-ttt/bin/python seed_robustness.py --plot-only )
    ;;
  gate-ins-submit)
    ssh "$HOST" "mkdir -p $REMOTE_DIR/slurm_logs $REMOTE_DIR/gate_insertion_results"
    rsync -av "$LOCAL_DIR/sweep.py" "$LOCAL_DIR/gate_insertion.py" \
              "$LOCAL_DIR/../initial_program.py" \
              "$LOCAL_DIR/cluster/gate_insertion_array.sbatch" "$HOST:$REMOTE_DIR/"
    ssh "$HOST" "cd $REMOTE_DIR && sbatch gate_insertion_array.sbatch"
    ;;
  gate-ins-status)
    ssh "$HOST" "squeue --me; echo '--- finished gate-ins jobs ---'; ls $REMOTE_DIR/gate_insertion_results 2>/dev/null | wc -l"
    ;;
  gate-ins-fetch)
    rsync -av "$HOST:$REMOTE_DIR/gate_insertion_results/" "$LOCAL_DIR/gate_insertion_results/"
    ( cd "$LOCAL_DIR" && ../.venv-shinka-ttt/bin/python gate_insertion.py --plot-only )
    ;;
  frozen-submit)
    ssh "$HOST" "mkdir -p $REMOTE_DIR/slurm_logs $REMOTE_DIR/base_optima $REMOTE_DIR/gate_insertion_frozen_results"
    rsync -av "$LOCAL_DIR/sweep.py" "$LOCAL_DIR/gate_insertion_frozen.py" \
              "$LOCAL_DIR/../initial_program.py" \
              "$LOCAL_DIR/cluster/gate_frozen_base_array.sbatch" \
              "$LOCAL_DIR/cluster/gate_frozen_insert_array.sbatch" "$HOST:$REMOTE_DIR/"
    JIDA=$(ssh "$HOST" "cd $REMOTE_DIR && sbatch gate_frozen_base_array.sbatch" | awk '{print $NF}')
    JIDB=$(ssh "$HOST" "cd $REMOTE_DIR && sbatch --dependency=afterok:$JIDA gate_frozen_insert_array.sbatch" | awk '{print $NF}')
    echo "Submitted frozen-base=$JIDA  frozen-insert=$JIDB (insert waits on base)"
    ;;
  frozen-status)
    ssh "$HOST" "squeue --me; echo '--- base_optima done ---'; ls $REMOTE_DIR/base_optima 2>/dev/null | wc -l; echo '--- insertion results done ---'; find $REMOTE_DIR/gate_insertion_frozen_results -name '*.json' 2>/dev/null | wc -l"
    ;;
  frozen-fetch)
    rsync -av "$HOST:$REMOTE_DIR/base_optima/" "$LOCAL_DIR/base_optima/"
    rsync -av "$HOST:$REMOTE_DIR/gate_insertion_frozen_results/" "$LOCAL_DIR/gate_insertion_frozen_results/"
    ( cd "$LOCAL_DIR" && ../.venv-shinka-ttt/bin/python gate_insertion_frozen.py --plot-only )
    ;;
  ea-submit)
    ssh "$HOST" "mkdir -p $REMOTE_DIR/slurm_logs $REMOTE_DIR/ea_robustness_histories $REMOTE_DIR/ea_gate_insertion_results $REMOTE_DIR/ea_programs"
    rsync -av "$LOCAL_DIR/ea_seed_robustness.py" "$LOCAL_DIR/ea_gate_insertion.py" \
              "$LOCAL_DIR/../initial_program.py" \
              "$LOCAL_DIR/ea_programs/" \
              "$LOCAL_DIR/cluster/ea_robustness_array.sbatch" \
              "$LOCAL_DIR/cluster/ea_gate_insertion_array.sbatch" \
              "$HOST:$REMOTE_DIR/"
    JID1=$(ssh "$HOST" "cd $REMOTE_DIR && sbatch ea_robustness_array.sbatch" | awk '{print $NF}')
    JID2=$(ssh "$HOST" "cd $REMOTE_DIR && sbatch ea_gate_insertion_array.sbatch" | awk '{print $NF}')
    echo "Submitted ea_robustness=$JID1  ea_gate_insertion=$JID2"
    ;;
  ea-status)
    ssh "$HOST" "squeue --me --jobs \$(squeue --me -h -o '%i' | paste -sd,) 2>/dev/null | grep -E 'ea_rob|ea_gate' || echo '(no EA jobs queued)'; echo '--- ea_robustness done ---'; ls $REMOTE_DIR/ea_robustness_histories 2>/dev/null | wc -l; echo '--- ea_gate_ins done ---'; ls $REMOTE_DIR/ea_gate_insertion_results 2>/dev/null | wc -l"
    ;;
  ea-fetch)
    rsync -av "$HOST:$REMOTE_DIR/ea_robustness_histories/"   "$LOCAL_DIR/ea_robustness_histories/"
    rsync -av "$HOST:$REMOTE_DIR/ea_gate_insertion_results/" "$LOCAL_DIR/ea_gate_insertion_results/"
    ( cd "$LOCAL_DIR" && ../.venv-shinka-ttt/bin/python ea_seed_robustness.py --plot-only )
    ( cd "$LOCAL_DIR" && ../.venv-shinka-ttt/bin/python ea_gate_insertion.py  --plot-only )
    ;;
  # ── SU2-like evolved ansatz (converged ShinkaEvolve winner) ─────────────────
  su2-sweep-submit)
    ssh "$HOST" "mkdir -p $REMOTE_DIR/slurm_logs $REMOTE_DIR/histories_ea"
    rsync -av "$LOCAL_DIR/sweep.py" "$LOCAL_DIR/sweep_ea.py" \
              "$LOCAL_DIR/../initial_program.py" \
              "$LOCAL_DIR/cluster/su2_sweep_array.sbatch" "$HOST:$REMOTE_DIR/"
    ssh "$HOST" "cd $REMOTE_DIR && sbatch su2_sweep_array.sbatch"
    ;;
  su2-sweep-status)
    ssh "$HOST" "squeue --me; echo '--- su2 sweep histories ---'; ls $REMOTE_DIR/histories_ea 2>/dev/null | wc -l"
    ;;
  su2-sweep-fetch)
    rsync -av "$HOST:$REMOTE_DIR/histories_ea/" "$LOCAL_DIR/histories_ea/"
    ( cd "$LOCAL_DIR" && ../.venv-shinka-ttt/bin/python sweep_ea.py --plot-only )
    ;;
  su2-robustness-submit)
    ssh "$HOST" "mkdir -p $REMOTE_DIR/slurm_logs $REMOTE_DIR/robustness_histories_ea"
    rsync -av "$LOCAL_DIR/sweep.py" "$LOCAL_DIR/sweep_ea.py" "$LOCAL_DIR/seed_robustness_ea.py" \
              "$LOCAL_DIR/../initial_program.py" \
              "$LOCAL_DIR/cluster/su2_robustness_array.sbatch" "$HOST:$REMOTE_DIR/"
    ssh "$HOST" "cd $REMOTE_DIR && sbatch su2_robustness_array.sbatch"
    ;;
  su2-robustness-status)
    ssh "$HOST" "squeue --me; echo '--- su2 robustness seeds ---'; ls $REMOTE_DIR/robustness_histories_ea 2>/dev/null | wc -l"
    ;;
  su2-robustness-fetch)
    rsync -av "$HOST:$REMOTE_DIR/robustness_histories_ea/" "$LOCAL_DIR/robustness_histories_ea/"
    ( cd "$LOCAL_DIR" && ../.venv-shinka-ttt/bin/python seed_robustness_ea.py --plot-only )
    ;;
  su2-frozen-submit)
    ssh "$HOST" "mkdir -p $REMOTE_DIR/slurm_logs $REMOTE_DIR/base_optima_ea $REMOTE_DIR/gate_insertion_frozen_ea_results"
    rsync -av "$LOCAL_DIR/sweep.py" "$LOCAL_DIR/sweep_ea.py" "$LOCAL_DIR/gate_insertion_frozen_ea.py" \
              "$LOCAL_DIR/../initial_program.py" \
              "$LOCAL_DIR/cluster/su2_frozen_base_array.sbatch" \
              "$LOCAL_DIR/cluster/su2_frozen_insert_array.sbatch" "$HOST:$REMOTE_DIR/"
    JIDA=$(ssh "$HOST" "cd $REMOTE_DIR && sbatch su2_frozen_base_array.sbatch" | awk '{print $NF}')
    JIDB=$(ssh "$HOST" "cd $REMOTE_DIR && sbatch --dependency=afterok:$JIDA su2_frozen_insert_array.sbatch" | awk '{print $NF}')
    echo "Submitted su2-frozen-base=$JIDA  su2-frozen-insert=$JIDB (insert waits on base)"
    ;;
  su2-frozen-status)
    ssh "$HOST" "squeue --me; echo '--- su2 base_optima done ---'; ls $REMOTE_DIR/base_optima_ea 2>/dev/null | wc -l; echo '--- su2 insertion results done ---'; find $REMOTE_DIR/gate_insertion_frozen_ea_results -name '*.json' 2>/dev/null | wc -l"
    ;;
  su2-frozen-fetch)
    rsync -av "$HOST:$REMOTE_DIR/base_optima_ea/" "$LOCAL_DIR/base_optima_ea/"
    rsync -av "$HOST:$REMOTE_DIR/gate_insertion_frozen_ea_results/" "$LOCAL_DIR/gate_insertion_frozen_ea_results/"
    ( cd "$LOCAL_DIR" && ../.venv-shinka-ttt/bin/python gate_insertion_frozen_ea.py --plot-only )
    ;;
  # ── 07-03 meeting follow-up: overfitting control + perturbation + degeneracy ──
  # (cemoid track). Submits were done manually; these targets cover status/fetch.
  meeting-submit)
    ssh "$HOST" "mkdir -p $REMOTE_DIR/slurm_logs $REMOTE_DIR/joint_nogate_results $REMOTE_DIR/perturbation_results $REMOTE_DIR/degeneracy_results"
    rsync -av "$LOCAL_DIR/sweep.py" "$LOCAL_DIR/gate_insertion_frozen.py" \
              "$LOCAL_DIR/joint_nogate_baseline.py" "$LOCAL_DIR/perturbation_stability.py" \
              "$LOCAL_DIR/degeneracy_pca.py" "$LOCAL_DIR/../initial_program.py" \
              "$LOCAL_DIR/cluster/joint_nogate_array.sbatch" \
              "$LOCAL_DIR/cluster/perturbation_array.sbatch" \
              "$LOCAL_DIR/cluster/degeneracy_array.sbatch" "$HOST:$REMOTE_DIR/"
    J1=$(ssh "$HOST" "cd $REMOTE_DIR && sbatch joint_nogate_array.sbatch" | awk '{print $NF}')
    J2=$(ssh "$HOST" "cd $REMOTE_DIR && sbatch perturbation_array.sbatch" | awk '{print $NF}')
    J3=$(ssh "$HOST" "cd $REMOTE_DIR && sbatch degeneracy_array.sbatch" | awk '{print $NF}')
    echo "Submitted joint_nogate=$J1  perturbation=$J2  degeneracy=$J3"
    ;;
  meeting-status)
    ssh "$HOST" "squeue --me -o '%.10i %.8j %.8T'; \
      echo '--- joint_nogate done ---'; ls $REMOTE_DIR/joint_nogate_results/*.json 2>/dev/null | wc -l; \
      echo '--- perturbation done (of 210) ---'; find $REMOTE_DIR/perturbation_results -name '*.json' 2>/dev/null | wc -l; \
      echo '--- degeneracy done (of 500) ---'; find $REMOTE_DIR/degeneracy_results -name '*.json' 2>/dev/null | wc -l"
    ;;
  meeting-fetch)
    rsync -av "$HOST:$REMOTE_DIR/joint_nogate_results/"  "$LOCAL_DIR/joint_nogate_results/"
    rsync -av "$HOST:$REMOTE_DIR/perturbation_results/"  "$LOCAL_DIR/perturbation_results/"
    rsync -av "$HOST:$REMOTE_DIR/degeneracy_results/"    "$LOCAL_DIR/degeneracy_results/"
    ( cd "$LOCAL_DIR" && ../.venv-shinka-ttt/bin/python joint_nogate_baseline.py --plot-only )
    ( cd "$LOCAL_DIR" && ../.venv-shinka-ttt/bin/python perturbation_stability.py --plot-only )
    ( cd "$LOCAL_DIR" && ../.venv-shinka-ttt/bin/python degeneracy_pca.py --analyze )
    ;;
  *)
    echo "usage: $0 {setup|submit|status|fetch|sweep-ext-submit|sweep-ext-status|sweep-ext-fetch|robustness-submit|robustness-status|robustness-fetch|gate-ins-submit|gate-ins-status|gate-ins-fetch|ea-submit|ea-status|ea-fetch|su2-sweep-{submit,status,fetch}|su2-robustness-{submit,status,fetch}|su2-frozen-{submit,status,fetch}|meeting-{submit,status,fetch}}"
    exit 1
    ;;
esac
