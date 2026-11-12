#!/usr/bin/env bash
# Submit the three OpenRouter-routed ensemble arms for transfer-sn.
#
# Rosters are disjoint by construction and each arm is three distinct vendors
# (see transfer-sn/make_openrouter_configs.py for the reasoning). This replaces
# the az_* arms, whose mid and frontier pools shared 2 of 3 members.
#
#   arm       models                                          effort    cap
#   weak      gpt-5.4-nano / gemini-3.1-flash-lite / qwen3-coder   low     $10
#   mid       gpt-5.4-mini / gemini-3-flash / claude-haiku-4.5     medium  $15
#   frontier  gpt-5.6-sol / claude-opus-4.6 / gemini-3.1-pro       xhigh   $30
#
# Reasoning effort is tiered WITH the arm on purpose: the comparison spans model
# capability and reasoning budget together, since a top model at low effort is
# not a frontier proposer. Arms therefore differ in two respects by design.
#
# 50 generations. At the measured xhigh cost of ~$0.30/generation the frontier
# arm lands near $15, so none of the caps bind.
#
# claude-opus-4.7 was the original frontier pick and was replaced by 4.6: it
# returns reasoning_tokens=0 at every effort level and with an explicit thinking
# budget (probe_anthropic_reasoning.py).
#
# orch_zc.sbatch is the OpenRouter orchestrator: it reads $HOME/.openrouter_key
# (mode 600) so the key never appears in job args or scontrol output.
#
# Usage:  ./launch_or_ens.sh [generations]      (run ON the Bouchet login node)
set -euo pipefail

GENERATIONS="${1:-50}"
TASKDIR="$HOME/project/transfer_sn"

if [ ! -r "$HOME/.openrouter_key" ]; then
    echo "missing $HOME/.openrouter_key (mode 600)" >&2
    exit 1
fi

# Refuse before submitting anything if ANY arm would clobber existing results,
# so we never end up with a half-submitted set.
for ARM in weak mid frontier; do
    CONFIG="shinka_config_or_${ARM}_r1.json"
    RESULTS="results_or_${ARM}_r1"
    if [ ! -f "$TASKDIR/$CONFIG" ]; then
        echo "missing $TASKDIR/$CONFIG" >&2
        exit 1
    fi
    if [ -d "$TASKDIR/$RESULTS" ]; then
        echo "refusing to overwrite existing $TASKDIR/$RESULTS" >&2
        exit 1
    fi
done

for ARM in weak mid frontier; do
    JOB="or_${ARM}_r1"
    sbatch --job-name="$JOB" \
           --chdir="$TASKDIR" \
           --output="$HOME/project/orch_${JOB}_%j.out" \
           "$HOME/project/orch_zc.sbatch" \
           "shinka_config_or_${ARM}_r1.json" "results_or_${ARM}_r1" "$GENERATIONS"
done

echo
echo "submitted 3 OpenRouter ensemble arms at $GENERATIONS generations"
squeue -u "$USER" -o "%.10i %.22j %.8T %.10M"
