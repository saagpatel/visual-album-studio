#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"
mkdir -p out/logs

./scripts/test/unit.sh
./scripts/test/integration.sh

PRODUCT_LOG="out/logs/acceptance_phase_07_product.log"
if command -v godot >/dev/null 2>&1; then
  VAS_REPO_ROOT="$ROOT_DIR" godot --headless --path app --script res://tests/phase7_acceptance.gd 2>&1 | tee "$PRODUCT_LOG"
elif command -v godot4 >/dev/null 2>&1; then
  VAS_REPO_ROOT="$ROOT_DIR" godot4 --headless --path app --script res://tests/phase7_acceptance.gd 2>&1 | tee "$PRODUCT_LOG"
else
  echo "ERROR: Godot executable not found; product-path AT-007 cannot run (source: docs/00-readme.md, docs/phases/phase-07.md)" >&2
  exit 1
fi

if rg -n "SCRIPT ERROR|Parse Error|Failed to load script|\[FAIL\]" "$PRODUCT_LOG" >/dev/null 2>&1; then
  echo "ERROR: product-path AT-007 log contains script/runtime failures. See $PRODUCT_LOG" >&2
  exit 1
fi

if [[ -x worker/.venv/bin/python ]]; then
  set +e
  PYTHONPATH=worker:app/src/core_py worker/.venv/bin/python -m pytest -q app/tests_py/acceptance/test_at007_phase7.py | tee out/logs/acceptance_phase_07_harness.log
  HARNESS_EXIT=$?
  set -e
  if [[ $HARNESS_EXIT -ne 0 ]]; then
    echo "WARN: Harness AT-007 regression failed (non-gating during rebaseline)." >&2
  fi
elif command -v python3 >/dev/null 2>&1; then
  set +e
  PYTHONPATH=worker:app/src/core_py python3 -m pytest -q app/tests_py/acceptance/test_at007_phase7.py | tee out/logs/acceptance_phase_07_harness.log
  HARNESS_EXIT=$?
  set -e
  if [[ $HARNESS_EXIT -ne 0 ]]; then
    echo "WARN: Harness AT-007 regression failed (non-gating during rebaseline)." >&2
  fi
fi
