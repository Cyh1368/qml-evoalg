#!/usr/bin/env bash
# Single verification entry point for tic-tac-toe/ (no test suite exists).
# Compile-checks the driver/analysis scripts, validates config JSON, and
# smoke-imports the generated evaluator inside the project venv.
set -uo pipefail
cd "$(dirname "$0")/.."

PY=".venv-shinka-ttt/bin/python"
[ -x "$PY" ] || PY=python3
fail=0

echo "== compile check =="
for f in run_shinkaevolve_monitored.py evolution_server.py make_ansatz_report.py \
         display_circuit.py activate_shinkaevolve_visualization.py \
         shinka_cli_task/initial.py shinka_cli_task/evaluate.py \
         shinka_cluster/launch_shinka_cluster.py; do
  [ -f "$f" ] || continue
  "$PY" -m py_compile "$f" && echo "ok  $f" || { echo "FAIL $f"; fail=1; }
done

echo "== config JSON =="
"$PY" -c "import json; json.load(open('shinka_cli_task/shinka_config.json')); print('ok  shinka_config.json')" || fail=1

echo "== evaluator import smoke =="
"$PY" - <<'EOF' || fail=1
import importlib.util, sys
spec = importlib.util.spec_from_file_location("initial", "shinka_cli_task/initial.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
assert hasattr(m, "ANSATZ_SPEC"), "ANSATZ_SPEC missing from initial.py"
print("ok  initial.py imports; ANSATZ_SPEC present")
EOF

if [ "$fail" -ne 0 ]; then echo "VERIFY FAILED"; exit 1; fi
echo "VERIFY OK"
