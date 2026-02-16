#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <phase-number>" >&2
  exit 2
fi

PHASE="$1"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

mkdir -p out/logs

if [[ ! -f "docs/phases/phase-${PHASE}.md" ]]; then
  echo "ERROR: missing phase spec docs/phases/phase-${PHASE}.md" >&2
  exit 1
fi

./scripts/test/unit.sh
./scripts/test/integration.sh

echo "AT-${PHASE} placeholder gate executed" | tee "out/logs/acceptance_phase_${PHASE}.log"
