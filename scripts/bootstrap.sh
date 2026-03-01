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

if jq -e '.artifacts[]? | select((.sha256 // "") | test("REPLACE_WITH_PINNED_SHA256|^$"))' tools/ffmpeg/checksums.json >/dev/null; then
  echo "ERROR: tools/ffmpeg/checksums.json contains placeholder or empty sha256 values." >&2
  exit 1
fi

detect_platform() {
  local os arch
  os="$(uname -s | tr '[:upper:]' '[:lower:]')"
  arch="$(uname -m)"
  case "${os}-${arch}" in
    darwin-arm64) echo "darwin-arm64" ;;
    darwin-x86_64) echo "darwin-x86_64" ;;
    linux-x86_64) echo "linux-x86_64" ;;
    linux-aarch64) echo "linux-arm64" ;;
    *) echo "${os}-${arch}" ;;
  esac
}

verify_managed_ffmpeg_if_present() {
  local ffmpeg_version managed_root platform filename expected_sha candidate
  ffmpeg_version="$(jq -r '.ffmpeg.version // ""' tools/versions.json)"
  managed_root="$(jq -r '.ffmpeg.managed_root // "tools/ffmpeg"' tools/versions.json)"
  platform="$(detect_platform)"

  filename="$(jq -r --arg p "$platform" '.artifacts[]? | select(.platform == $p) | (.filename // "ffmpeg")' tools/ffmpeg/checksums.json | head -n 1)"
  expected_sha="$(jq -r --arg p "$platform" '.artifacts[]? | select(.platform == $p) | (.sha256 // "")' tools/ffmpeg/checksums.json | head -n 1)"
  if [[ -z "$filename" || -z "$expected_sha" ]]; then
    echo "WARN: no managed FFmpeg checksum entry for platform '$platform'."
    return 0
  fi

  candidate="$managed_root/$ffmpeg_version/$platform/$filename"

  if [[ -f "$candidate" ]]; then
    local actual_sha
    actual_sha="$(shasum -a 256 "$candidate" | awk '{print $1}')"
    if [[ "$actual_sha" != "$expected_sha" ]]; then
      echo "ERROR: managed FFmpeg checksum mismatch for $candidate" >&2
      echo "expected=$expected_sha actual=$actual_sha" >&2
      exit 1
    fi
    echo "Managed FFmpeg verified: $candidate"
  else
    echo "WARN: managed FFmpeg not found at $candidate; falling back to PATH ffmpeg if available."
  fi
}

verify_managed_ffmpeg_if_present

python3 -m venv worker/.venv
source worker/.venv/bin/activate
python -m pip install --upgrade pip >/dev/null
if [[ -f worker/requirements.lock ]]; then
  python -m pip install -r worker/requirements.lock >/dev/null
fi
python -m pip install bandit pip-audit >/dev/null

cargo build --manifest-path native/vas_keyring/Cargo.toml >/dev/null
if ! cargo audit --version >/dev/null 2>&1; then
  cargo install cargo-audit --locked >/dev/null
fi

if command -v ffmpeg >/dev/null 2>&1; then
  ffmpeg_path="$(command -v ffmpeg)"
  ffmpeg_sha="$(shasum -a 256 "$ffmpeg_path" | awk '{print $1}')"
  ffmpeg -version | head -n 1 > out/logs/ffmpeg_version.txt
  {
    echo "path=$ffmpeg_path"
    echo "sha256=$ffmpeg_sha"
  } > out/logs/ffmpeg_binary.txt
else
  echo "WARN: ffmpeg not found on PATH. Install or place managed binary under tools/ffmpeg." | tee out/logs/ffmpeg_missing.warn
fi

echo "Bootstrap complete"
