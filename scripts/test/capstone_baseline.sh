#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

OUT_DIR="out/logs/capstone_baseline"
mkdir -p "$OUT_DIR"

STAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")"
HEAD_SHA="$(git rev-parse HEAD 2>/dev/null || echo "unknown")"

{
  echo "timestamp_utc=$STAMP"
  echo "branch=$BRANCH"
  echo "head_sha=$HEAD_SHA"
  echo "pwd=$ROOT_DIR"
  echo "git_status_begin"
  git status --short --branch || true
  echo "git_status_end"
} | tee "$OUT_DIR/git_snapshot.txt"

git ls-files > "$OUT_DIR/tracked_files.txt"
git status --porcelain > "$OUT_DIR/git_status_porcelain.txt" || true

echo "Capstone baseline snapshot written to $OUT_DIR"
