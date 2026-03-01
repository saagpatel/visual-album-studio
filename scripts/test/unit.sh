#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

mkdir -p out/logs

KEYRING_BIN="native/vas_keyring/target/debug/vas_keyring"
if [[ ! -x "$KEYRING_BIN" ]]; then
  if ! command -v cargo >/dev/null 2>&1; then
    echo "ERROR: cargo is required to build $KEYRING_BIN (source: docs/00-readme.md)" >&2
    exit 1
  fi
  echo "Building keyring helper binary for unit tests..."
  cargo build --manifest-path native/vas_keyring/Cargo.toml >/dev/null
fi

if [[ ! -x "$KEYRING_BIN" ]]; then
  echo "ERROR: failed to produce keyring helper at $KEYRING_BIN" >&2
  exit 1
fi

if [[ -d worker/tests ]]; then
  if [[ -x worker/.venv/bin/python ]]; then
    PYTHONPATH=worker:app/src/core_py worker/.venv/bin/python -m pytest -q worker/tests app/tests_py/unit | tee out/logs/unit_worker.log
  elif command -v python3 >/dev/null 2>&1; then
    PYTHONPATH=worker:app/src/core_py python3 -m pytest -q worker/tests app/tests_py/unit | tee out/logs/unit_worker.log
  else
    echo "ERROR: python3 unavailable for unit tests" >&2
    exit 1
  fi
fi

echo "Unit test suite complete"
