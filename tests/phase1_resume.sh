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
SQLITE_FIXTURE_ROOT="$(mktemp -d "$TEMP_PARENT/vas-resume-sqlite-XXXXXX")"

cleanup_fixture() {
  local resolved_root resolved_parent
  python3 - "$FIXTURE_ROOT" "$SQLITE_FIXTURE_ROOT" <<'PY'
import shutil
import sys
from pathlib import Path

for value, prefix in zip(sys.argv[1:], ("vas-resume-fixture-", "vas-resume-sqlite-")):
    path = Path(value)
    if path.is_symlink() or not path.name.startswith(prefix) or str(path.parent) not in ("/private/tmp", "/tmp"):
        raise SystemExit("refusing to clean an unexpected fixture path")
    if (path / "PRESERVE_FIXTURE_CHILD_RUNNING").exists():
        print(f"Preserving fixture with a child that may still be running: {path}", file=sys.stderr)
        continue
    if path.is_dir():
        shutil.rmtree(path)
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

if TEST_OUTPUT="$(VAS_RESUME_SQLITE_FIXTURE_ROOT="$SQLITE_FIXTURE_ROOT" VAS_GODOT_BIN="$GODOT_BIN" \
  "$GODOT_BIN" --headless --path app --script res://tests/phase1_resume_sqlite_test.gd 2>&1)"; then
  TEST_STATUS=0
else
  TEST_STATUS=$?
fi
printf '%s\n' "$TEST_OUTPUT"
if [[ "$TEST_STATUS" -ne 0 ]]; then
  exit "$TEST_STATUS"
fi
if printf '%s\n' "$TEST_OUTPUT" | rg -n "SCRIPT ERROR|Parse Error|Failed to load script|\[FAIL\]" >/dev/null 2>&1; then
  echo "ERROR: Phase 1 SQLite recovery fixture log contains failures" >&2
  exit 1
fi
