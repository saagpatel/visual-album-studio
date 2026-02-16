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
  echo "ERROR: python unavailable for determinism rerun" >&2
  exit 1
fi

PYTHONPATH=worker:app/src/core_py "$PY" -m pytest -q \
  app/tests_py/acceptance/test_at001_phase1.py \
  app/tests_py/unit/test_ts002_mapping_determinism.py \
  app/tests_py/unit/test_ts016_packaging_manifest.py \
  | tee "$OUT_DIR/determinism_rerun.log"

echo "Determinism rerun checks complete"
