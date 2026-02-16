#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

if command -v godot4 >/dev/null 2>&1; then
  exec godot4 --path app
elif command -v godot >/dev/null 2>&1; then
  exec godot --path app
else
  echo "ERROR: Godot executable not found (source: docs/00-readme.md)" >&2
  exit 1
fi
