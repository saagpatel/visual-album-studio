#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"
mkdir -p out/logs
./scripts/test/unit.sh
./scripts/test/integration.sh
if [[ -x worker/.venv/bin/python ]]; then
  PYTHONPATH=worker:app/src/core_py worker/.venv/bin/python -m pytest -q app/tests_py/acceptance/test_at002_phase2.py | tee out/logs/acceptance_phase_02.log
else
  PYTHONPATH=worker:app/src/core_py python3 -m pytest -q app/tests_py/acceptance/test_at002_phase2.py | tee out/logs/acceptance_phase_02.log
fi
