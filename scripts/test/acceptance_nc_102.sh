#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

mkdir -p out/logs
LOG_PATH="out/logs/acceptance_nc_102.log"
TEST_PATH="app/tests_py/acceptance/test_atnc_102_scheduler_simulation_dashboard.py"

if [[ ! -f "$TEST_PATH" ]]; then
  echo "ERROR: missing required next-cycle acceptance test: $TEST_PATH" >&2
  echo "Implement AT-NC-102 suite before running this gate." >&2
  exit 2
fi

if [[ ! -x worker/.venv/bin/python ]]; then
  ./scripts/bootstrap.sh
fi

if [[ -x worker/.venv/bin/python ]]; then
  PYTHONPATH=worker:app/src/core_py worker/.venv/bin/python -m pytest -q "$TEST_PATH" | tee "$LOG_PATH"
elif command -v python3 >/dev/null 2>&1; then
  PYTHONPATH=worker:app/src/core_py python3 -m pytest -q "$TEST_PATH" | tee "$LOG_PATH"
else
  echo "ERROR: python runtime unavailable for AT-NC-102" >&2
  exit 1
fi
