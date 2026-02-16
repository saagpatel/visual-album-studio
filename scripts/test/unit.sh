#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

mkdir -p out/logs

if [[ -d worker/tests ]]; then
  if [[ -x worker/.venv/bin/python ]]; then
    PYTHONPATH=worker worker/.venv/bin/python -m pytest -q worker/tests | tee out/logs/unit_worker.log
  elif command -v python3 >/dev/null 2>&1; then
    PYTHONPATH=worker python3 -m pytest -q worker/tests | tee out/logs/unit_worker.log
  else
    echo "ERROR: python3 unavailable for unit tests" >&2
    exit 1
  fi
fi

echo "Unit test suite complete"
