#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -n "${VAS_GODOT_BIN:-}" ]]; then
  GODOT_BIN="$VAS_GODOT_BIN"
elif [[ -x "$ROOT_DIR/out/tools/godot44/bin/godot" ]]; then
  GODOT_BIN="$ROOT_DIR/out/tools/godot44/bin/godot"
elif command -v godot >/dev/null 2>&1; then
  GODOT_BIN="$(command -v godot)"
elif command -v godot4 >/dev/null 2>&1; then
  GODOT_BIN="$(command -v godot4)"
else
  echo "ERROR: pinned Godot 4.4 is required for Phase 1 resume coverage" >&2
  exit 1
fi

if [[ ! -x "$GODOT_BIN" ]]; then
  echo "ERROR: VAS_GODOT_BIN is not executable: $GODOT_BIN" >&2
  exit 1
fi
GODOT_VERSION="$("$GODOT_BIN" --version)"
if [[ "$GODOT_VERSION" != 4.4.* ]]; then
  echo "ERROR: Phase 1 resume coverage requires Godot 4.4.x; found $GODOT_VERSION" >&2
  exit 1
fi

if [[ -d /private/tmp && -w /private/tmp ]]; then
  TEMP_PARENT="/private/tmp"
else
  TEMP_PARENT="/tmp"
fi
FIXTURE_ROOT="$(mktemp -d "$TEMP_PARENT/vas-resume-fixture-XXXXXX")"

cleanup_fixture() {
  local resolved_root resolved_parent
  resolved_root="$(cd "$FIXTURE_ROOT" 2>/dev/null && pwd -P)" || return 0
  resolved_parent="$(dirname "$resolved_root")"
  python3 - "$resolved_root" "$resolved_parent" <<'PY'
import shutil
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve(strict=True)
parent = Path(sys.argv[2]).resolve(strict=True)
if root.parent != parent or not root.name.startswith("vas-resume-fixture-"):
    raise SystemExit("refusing to clean an unexpected fixture path")
shutil.rmtree(root)
PY
}
trap cleanup_fixture EXIT

if TEST_OUTPUT="$(VAS_RESUME_FIXTURE_ROOT="$FIXTURE_ROOT" \
  "$GODOT_BIN" --headless --path app --script res://tests/phase1_resume_test.gd 2>&1)"; then
  TEST_STATUS=0
else
  TEST_STATUS=$?
fi
printf '%s\n' "$TEST_OUTPUT"
if [[ "$TEST_STATUS" -ne 0 ]]; then
  exit "$TEST_STATUS"
fi
if printf '%s\n' "$TEST_OUTPUT" | rg -n "SCRIPT ERROR|Parse Error|Failed to load script|\[FAIL\]" >/dev/null 2>&1; then
  echo "ERROR: Phase 1 resume fixture log contains script or assertion failures" >&2
  exit 1
fi
