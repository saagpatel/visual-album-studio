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

echo "Integration sanity checks complete" | tee out/logs/integration.log
