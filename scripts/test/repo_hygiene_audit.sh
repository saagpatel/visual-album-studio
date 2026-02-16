#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

OUT_DIR="out/logs/capstone_baseline"
mkdir -p "$OUT_DIR"
REPORT="$OUT_DIR/repo_hygiene_report.txt"
REPORT_ABS="$ROOT_DIR/$REPORT"

exec > >(tee "$REPORT_ABS") 2>&1

FAIL=0

echo "repo_hygiene_audit_started=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
echo "head_sha=$(git rev-parse HEAD 2>/dev/null || echo unknown)"

echo ""
echo "[tracked_forbidden_paths]"
while IFS= read -r path; do
  if [[ "$path" == out/* || "$path" == app/.godot/* || "$path" == worker/.venv/* || "$path" == native/vas_keyring/target/* || "$path" == logs/* ]]; then
    echo "forbidden_tracked=$path"
    FAIL=1
  fi
  if [[ "$path" == app/*.import || "$path" == app/*/*.import || "$path" == app/*/*/*.import ]]; then
    echo "forbidden_tracked=$path"
    FAIL=1
  fi
  if [[ "$path" == tools/ffmpeg/* && "$path" != tools/ffmpeg/checksums.json ]]; then
    echo "forbidden_tracked=$path"
    FAIL=1
  fi
done < <(git ls-files)

echo ""
echo "[tracked_large_files_over_20mb]"
while IFS= read -r path; do
  if [[ -f "$path" ]]; then
    size_bytes=$(wc -c < "$path" | tr -d ' ')
    if [[ "$size_bytes" -gt 20971520 ]]; then
      echo "large_tracked_file=$path size_bytes=$size_bytes"
      FAIL=1
    fi
  fi
done < <(git ls-files)

echo ""
echo "[gitignore_checks]"
for required in "out/**" "app/.godot/**" "app/**/*.import" "tools/ffmpeg/**" "worker/.venv/**" "native/vas_keyring/target/**" ".codex_audit/**"; do
  if rg -n --fixed-strings "$required" .gitignore >/dev/null 2>&1; then
    echo "present=$required"
  else
    echo "missing=$required"
    FAIL=1
  fi
done

echo ""
echo "[working_tree_status]"
git status --short --branch || true

if [[ "$FAIL" -ne 0 ]]; then
  echo "Repo hygiene audit failed. See $REPORT_ABS" >&2
  exit 1
fi

echo "Repo hygiene audit passed. See $REPORT_ABS"
