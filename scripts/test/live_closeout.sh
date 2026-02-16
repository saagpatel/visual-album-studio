#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

set +e
./scripts/test/live_phase_05.sh
P5=$?
./scripts/test/live_phase_06.sh
P6=$?
set -e

if [[ $P5 -eq 0 && $P6 -eq 0 ]]; then
  echo "Live closeout passed for Phase 5 and Phase 6"
  exit 0
fi

if [[ $P5 -eq 2 || $P6 -eq 2 ]]; then
  echo "Live closeout pending: missing credentials/prerequisites" >&2
  exit 2
fi

echo "Live closeout failed" >&2
exit 1
