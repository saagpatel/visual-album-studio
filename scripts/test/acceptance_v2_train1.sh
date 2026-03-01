#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

mkdir -p out/logs
LOG_PATH="out/logs/acceptance_v2_train1.log"

export VAS_RELEASE_SIGNING_KEY="${VAS_RELEASE_SIGNING_KEY:-train1-ci-signing-key}"

if [[ ! -x worker/.venv/bin/python ]]; then
  ./scripts/bootstrap.sh
fi

if [[ -x worker/.venv/bin/python ]]; then
  PYTHONPATH=worker:app/src/core_py worker/.venv/bin/python -m pytest -q app/tests_py/acceptance/test_atv2101_train1.py | tee "$LOG_PATH"
elif command -v python3 >/dev/null 2>&1; then
  PYTHONPATH=worker:app/src/core_py python3 -m pytest -q app/tests_py/acceptance/test_atv2101_train1.py | tee "$LOG_PATH"
else
  echo "ERROR: python runtime unavailable for AT-V2-101" >&2
  exit 1
fi
