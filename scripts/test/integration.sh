#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

mkdir -p out/logs

# Lightweight integration sanity checks for Phase 0.
for path in app/project.godot worker/pyproject.toml native/vas_keyring/Cargo.toml tools/versions.json; do
  if [[ ! -f "$path" ]]; then
    echo "ERROR: missing required file $path" >&2
    exit 1
  fi
done

if [[ -x worker/.venv/bin/python ]]; then
  PYTHONPATH=worker:app/src/core_py worker/.venv/bin/python -m pytest -q app/tests_py/integration | tee out/logs/integration_py.log
elif command -v python3 >/dev/null 2>&1; then
  PYTHONPATH=worker:app/src/core_py python3 -m pytest -q app/tests_py/integration | tee out/logs/integration_py.log
else
  echo "ERROR: python3 unavailable for integration tests" >&2
  exit 1
fi

echo "Integration sanity checks complete" | tee out/logs/integration.log
