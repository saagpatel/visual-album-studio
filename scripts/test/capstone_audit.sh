#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

OUT_DIR="out/logs/capstone_baseline"
mkdir -p "$OUT_DIR"
SUMMARY="$OUT_DIR/capstone_summary.txt"

FAIL=0

run_step() {
  local name="$1"
  shift
  echo "== $name ==" | tee -a "$SUMMARY"
  if "$@" | tee -a "$SUMMARY"; then
    echo "result[$name]=pass" | tee -a "$SUMMARY"
  else
    local rc=$?
    echo "result[$name]=fail exit_code=$rc" | tee -a "$SUMMARY"
    FAIL=1
  fi
  echo "" | tee -a "$SUMMARY"
}

echo "capstone_started=$(date -u +"%Y-%m-%dT%H:%M:%SZ")" > "$SUMMARY"
echo "branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)" >> "$SUMMARY"
echo "head_sha=$(git rev-parse HEAD 2>/dev/null || echo unknown)" >> "$SUMMARY"
echo "" >> "$SUMMARY"

run_step "baseline_snapshot" ./scripts/test/capstone_baseline.sh
run_step "bootstrap" ./scripts/bootstrap.sh
run_step "unit" ./scripts/test/unit.sh
run_step "integration" ./scripts/test/integration.sh
run_step "acceptance_phase_01" ./scripts/test/acceptance_phase_01.sh
run_step "acceptance_phase_02" ./scripts/test/acceptance_phase_02.sh
run_step "acceptance_phase_03" ./scripts/test/acceptance_phase_03.sh
run_step "acceptance_phase_04" ./scripts/test/acceptance_phase_04.sh
run_step "acceptance_phase_05" ./scripts/test/acceptance_phase_05.sh
run_step "acceptance_phase_06" ./scripts/test/acceptance_phase_06.sh
run_step "acceptance_phase_07" ./scripts/test/acceptance_phase_07.sh
run_step "determinism_rerun" ./scripts/test/determinism_rerun.sh
run_step "reliability_longrun" ./scripts/test/reliability_longrun.sh
run_step "security_audit" ./scripts/test/security_audit.sh
run_step "repo_hygiene_audit" ./scripts/test/repo_hygiene_audit.sh

echo "== live_closeout ==" | tee -a "$SUMMARY"
PRESET_VAS_YT_TEST_VIDEO_PATH="${VAS_YT_TEST_VIDEO_PATH:-}"
if [[ -f "./scripts/test/live.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source ./scripts/test/live.env
  set +a
fi
if [[ -n "$PRESET_VAS_YT_TEST_VIDEO_PATH" ]]; then
  export VAS_YT_TEST_VIDEO_PATH="$PRESET_VAS_YT_TEST_VIDEO_PATH"
fi
set +e
./scripts/test/live_closeout.sh | tee -a "$SUMMARY"
LIVE_RC=$?
set -e
if [[ "$LIVE_RC" -eq 0 ]]; then
  echo "result[live_closeout]=pass" | tee -a "$SUMMARY"
elif [[ "$LIVE_RC" -eq 2 ]]; then
  echo "result[live_closeout]=pending_prerequisites" | tee -a "$SUMMARY"
else
  echo "result[live_closeout]=fail exit_code=$LIVE_RC" | tee -a "$SUMMARY"
  FAIL=1
fi

echo "" | tee -a "$SUMMARY"
echo "capstone_finished=$(date -u +"%Y-%m-%dT%H:%M:%SZ")" | tee -a "$SUMMARY"

if [[ "$FAIL" -ne 0 ]]; then
  echo "Capstone audit failed. See $SUMMARY" >&2
  exit 1
fi

echo "Capstone audit completed successfully. See $SUMMARY"
