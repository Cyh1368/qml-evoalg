#!/usr/bin/env bash
# Status of the transfer-sn multi-provider ensemble arms.
#
# The comparison target is the solo gpt-5.6-sol arm in results_gpt56sol_r2,
# which first reached the equivariant solution at generation 33 (0.8713 ->
# 0.9372) and stopped at generation 63 on its $10 cap.
#
# Usage:  ~/project/ens3_status.sh
set -uo pipefail
TASKDIR="$HOME/project/transfer_sn"
ARMS="${ARMS:-az_weak_r1 az_mid_r1 az_frontier_r1}"

echo "=== SLURM ==="
squeue -u "$USER" -o "%.10i %.22j %.8T %.10M" | tail -12

for R in $ARMS; do
    D="$TASKDIR/results_$R"
    L="$D/evolution_run.log"
    echo
    echo "=================== $R ==================="
    [ -f "$L" ] || { echo "  not started"; continue; }

    echo "--- budget / generations ---"
    grep -aoE 'total: \$[0-9.]+ \([0-9.]+%\)' "$L" | tail -1
    grep -aoE 'added \(gen [0-9]+\)' "$L" | tail -1
    grep -aE 'API cost budget reached' "$L" | tail -1

    # Count only real proposer queries. A bare grep for the model string also
    # matches the bandit posterior table (reprinted every round with all three
    # arms) and the result panel's model_name row, which inflates the count
    # several-fold and makes the bandit look balanced before it has any data.
    echo "--- proposer queries per pipeline (bandit balance) ---"
    grep -aoE '==> QUERYING: \[.(openrouter/|azure-)[a-zA-Z0-9./-]*' "$L" \
        | sed -E 's@.*(openrouter/|azure-)@@' | grep -vE 'o4-mini|text-embedding' \
        | sort | uniq -c
    echo "--- eval pipeline (a generation lands only when its eval finishes) ---"
    printf '    submitted to eval: %s\n' \
        "$(grep -acE 'Proposal . Eval: gen [0-9]+ submitted' "$L")"
    grep -aoE 'Running jobs: [0-9]+/[0-9]+, Proposals: [0-9]+/[0-9]+' "$L" | tail -1 \
        | sed 's/^/    /'

    echo "--- best-so-far trajectory ---"
    python3 - "$D" <<'PY'
import sys, sqlite3, shutil, tempfile, os, glob
d = sys.argv[1]
src = os.path.join(d, "programs.sqlite")
if not os.path.exists(src):
    print("  no db yet"); raise SystemExit
# copy out of NFS: the live WAL db refuses concurrent readers there
tmp = tempfile.mkdtemp()
try:
    for f in glob.glob(src + "*"):
        shutil.copy(f, tmp)
    c = sqlite3.connect(os.path.join(tmp, "programs.sqlite"))
    rows = list(c.execute(
        "select generation, combined_score, metadata from programs order by generation"))
    if not rows:
        print("  no programs yet"); raise SystemExit
    print(f"  programs={len(rows)}  max_gen={max(r[0] for r in rows)}")
    import json

    def patch_name(meta):
        if not meta:
            return ""
        try:
            return (json.loads(meta) or {}).get("patch_name", "") or ""
        except Exception:
            return ""

    best = -9.0
    for g, s, meta in rows:
        if s is None:
            continue
        if s > best + 1e-9:
            best = s
            print(f"    gen {g:<4} new best {s:.4f}   {patch_name(meta)}")

    # Match ONLY patch_name. Matching the whole metadata blob is useless: it
    # embeds llm_result.content, so every program where the model merely says
    # the word "permutation" while thinking counts as a hit (48/49 on r1).
    hits = [(g, s, patch_name(m)) for g, s, m in rows
            if any(k in patch_name(m).lower()
                   for k in ("equivarian", "permutation", "symmetr"))]
    if hits:
        print(f"  symmetry-NAMED patches: {len(hits)}, first at gen {hits[0][0]}")
        for g, s, nm in hits[:4]:
            flag = "" if s is None or s < best - 1e-9 else "  <-- is current best"
            print(f"     gen {g:<4} {('  n/a' if s is None else f'{s:.4f}')}  {nm}{flag}")
    else:
        print("  no symmetry-named patch yet")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
PY
done

echo
echo "=== baseline: solo gpt-5.6-sol (results_gpt56sol_r2), RESCALED axis ==="
echo "    scores below are on the new scale: 0.0 = seed, 1.0 = best symmetric solution"
echo "    gen 0  0.000 | gen 27 0.179 | gen 33 0.882 <- permutation_equivariant_ansatz"
echo "    gen 36 0.918 | gen 51 1.000 | stopped gen 63 on the \$10 cap"
