#!/usr/bin/env bash
set -euo pipefail

required_files=(
  "docs/20-phase-blueprint-v2.md"
  "docs/03-requirements-v2.md"
  "docs/18-traceability-matrix-v2.md"
  "docs/25-ui-ux-standards-v2.md"
  "docs/adr/0001-v2-cloud-sync-architecture.md"
  "docs/adr/0002-v2-conflict-resolution-model.md"
  ".github/CODEOWNERS"
  ".github/dependabot.yml"
  ".github/workflows/codeql-analysis.yml"
  ".github/workflows/dependency-review.yml"
  ".github/workflows/release-provenance.yml"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "$file" ]]; then
    echo "V2 Train 0 gate failure: missing required file: $file" >&2
    exit 1
  fi
done

if ! grep -q "AT-V2-000" docs/20-phase-blueprint-v2.md; then
  echo "V2 Train 0 gate failure: missing AT-V2-000 gate reference in blueprint" >&2
  exit 1
fi

if ! grep -q "RQ-V2-001" docs/03-requirements-v2.md; then
  echo "V2 Train 0 gate failure: requirements ID baseline missing" >&2
  exit 1
fi

echo "V2 Train 0 governance gate passed."
