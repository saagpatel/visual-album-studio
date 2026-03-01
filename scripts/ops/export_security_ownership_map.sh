#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

OUT_DIR="out/logs/security"
OUT_MD="$OUT_DIR/security_ownership_map.md"
OUT_JSON="$OUT_DIR/security_ownership_map.json"
CODEOWNERS_FILE=".github/CODEOWNERS"
DATE_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
HEAD_SHA="$(git rev-parse HEAD 2>/dev/null || echo unknown)"

mkdir -p "$OUT_DIR"

default_owner="$(awk '/^\*/ {print $2; exit}' "$CODEOWNERS_FILE" 2>/dev/null || true)"
if [[ -z "$default_owner" ]]; then
  default_owner="@unassigned"
fi

owner_for_path() {
  local path="$1"
  local owner
  owner="$(awk -v p="$path" '$1 == p {print $2; exit}' "$CODEOWNERS_FILE" 2>/dev/null || true)"
  if [[ -z "$owner" ]]; then
    owner="$default_owner"
  fi
  printf '%s' "$owner"
}

PATHS=(
  "/.github/workflows/"
  "/docs/16-security-privacy.md"
  "/docs/19-risk-register.md"
  "/docs/security-waivers.json"
  "/native/vas_keyring/"
  "/app/src/core/"
  "/app/src/adapters/"
  "/scripts/test/"
)

cat > "$OUT_MD" <<EOF
# Security Ownership Map

- generated_at_utc: \`$DATE_UTC\`
- head_sha: \`$HEAD_SHA\`
- source: \`$CODEOWNERS_FILE\`

| Critical Path | Owner | Coverage |
|---|---|---|
EOF

printf '{\n' > "$OUT_JSON"
printf '  "generated_at_utc": "%s",\n' "$DATE_UTC" >> "$OUT_JSON"
printf '  "head_sha": "%s",\n' "$HEAD_SHA" >> "$OUT_JSON"
printf '  "source": "%s",\n' "$CODEOWNERS_FILE" >> "$OUT_JSON"
printf '  "entries": [\n' >> "$OUT_JSON"

for i in "${!PATHS[@]}"; do
  path="${PATHS[$i]}"
  owner="$(owner_for_path "$path")"

  printf '| `%s` | `%s` | security-critical |\n' "$path" "$owner" >> "$OUT_MD"

  comma=","
  if [[ "$i" -eq $((${#PATHS[@]} - 1)) ]]; then
    comma=""
  fi
  printf '    {"path":"%s","owner":"%s","coverage":"security-critical"}%s\n' "$path" "$owner" "$comma" >> "$OUT_JSON"
done

printf '  ]\n}\n' >> "$OUT_JSON"

echo "security_ownership_map_exported=$OUT_MD"
echo "security_ownership_map_exported_json=$OUT_JSON"
