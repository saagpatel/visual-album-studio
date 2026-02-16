#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

require_cmd() {
  local cmd="$1"
  local source_doc="$2"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: required command '$cmd' is missing. Source: $source_doc" >&2
    exit 1
  fi
}

mkdir -p out/tmp out/logs out/cache tools/ffmpeg

require_cmd jq "docs/06-repo-structure.md"
require_cmd python3 "docs/00-readme.md"
require_cmd cargo "docs/00-readme.md"

if [[ ! -f tools/versions.json ]]; then
  echo "ERROR: missing tools/versions.json (source: docs/06-repo-structure.md)" >&2
  exit 1
fi

if [[ ! -f tools/ffmpeg/checksums.json ]]; then
  echo "ERROR: missing tools/ffmpeg/checksums.json (source: docs/06-repo-structure.md)" >&2
  exit 1
fi

python3 -m venv worker/.venv
source worker/.venv/bin/activate
python -m pip install --upgrade pip >/dev/null
if [[ -f worker/requirements.lock ]]; then
  python -m pip install -r worker/requirements.lock >/dev/null
fi
python -m pip install -e worker >/dev/null

cargo build --manifest-path native/vas_keyring/Cargo.toml >/dev/null

if command -v ffmpeg >/dev/null 2>&1; then
  ffmpeg -version | head -n 1 > out/logs/ffmpeg_version.txt
else
  echo "WARN: ffmpeg not found on PATH. Install or place managed binary under tools/ffmpeg." | tee out/logs/ffmpeg_missing.warn
fi

echo "Bootstrap complete"
