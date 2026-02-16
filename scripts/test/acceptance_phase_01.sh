#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

mkdir -p out/logs

./scripts/test/unit.sh
./scripts/test/integration.sh

if [[ -x worker/.venv/bin/python ]]; then
  PYTHONPATH=worker:app/src/core_py worker/.venv/bin/python -m pytest -q app/tests_py/acceptance/test_at001_phase1.py | tee out/logs/acceptance_phase_01.log
elif command -v python3 >/dev/null 2>&1; then
  PYTHONPATH=worker:app/src/core_py python3 -m pytest -q app/tests_py/acceptance/test_at001_phase1.py | tee out/logs/acceptance_phase_01.log
else
  echo "ERROR: python3 unavailable for acceptance tests" >&2
  exit 1
fi
