#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

OUT_DIR="out/logs/capstone_baseline"
mkdir -p "$OUT_DIR"

if [[ -x worker/.venv/bin/python ]]; then
  PY=worker/.venv/bin/python
elif command -v python3 >/dev/null 2>&1; then
  PY=python3
else
  echo "ERROR: python unavailable for reliability longrun checks" >&2
  exit 1
fi

for run in 1 2 3; do
  echo "reliability_iteration=$run" | tee -a "$OUT_DIR/reliability_longrun.log"
  PYTHONPATH=worker:app/src/core_py "$PY" -m pytest -q \
    app/tests_py/integration/test_it003_segment_resume.py \
    app/tests_py/integration/test_it009_command_center.py \
    app/tests_py/integration/test_it010_relink_provenance.py \
    | tee -a "$OUT_DIR/reliability_longrun.log"
done

echo "Reliability long-run checks complete"
