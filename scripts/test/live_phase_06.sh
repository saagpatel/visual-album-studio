#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

mkdir -p out/logs

python3 scripts/test/live_validation.py 06 | tee out/logs/live_phase_06.log
EXIT_CODE=${PIPESTATUS[0]}

if [[ $EXIT_CODE -eq 0 ]]; then
  echo "Phase 6 live validation passed"
  exit 0
fi

if [[ $EXIT_CODE -eq 2 ]]; then
  echo "Phase 6 live validation pending (missing prerequisites)" >&2
  exit 2
fi

echo "Phase 6 live validation failed" >&2
exit 1
