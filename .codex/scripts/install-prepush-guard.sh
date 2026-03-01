#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HOOK_PATH="$ROOT_DIR/.git/hooks/pre-push"

cat > "$HOOK_PATH" <<'HOOK'
#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

if [[ "${CODEX_BYPASS_PREPUSH:-0}" == "1" ]]; then
  echo "[codex pre-push] bypass enabled via CODEX_BYPASS_PREPUSH=1"
  exit 0
fi

echo "[codex pre-push] running strict verify gate..."
env VAS_SECURITY_STRICT=1 bash .codex/scripts/run_verify_commands.sh
HOOK

chmod +x "$HOOK_PATH"
echo "Installed pre-push guard at $HOOK_PATH"
