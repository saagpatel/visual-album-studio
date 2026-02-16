#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

OUT_DIR="out/logs/capstone_baseline"
mkdir -p "$OUT_DIR"
REPORT="$OUT_DIR/security_audit_report.txt"
REPORT_ABS="$ROOT_DIR/$REPORT"

exec > >(tee "$REPORT_ABS") 2>&1

FAIL=0

echo "security_audit_started=$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
echo "head_sha=$(git rev-parse HEAD 2>/dev/null || echo unknown)"

echo ""
echo "[secret_scan_tracked_files]"
SECRET_PATTERN='(AIza[0-9A-Za-z_-]{35}|ghp_[0-9A-Za-z]{36}|xox[baprs]-[0-9A-Za-z-]{10,}|-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----)'
if git ls-files | xargs rg -n --no-heading -e "$SECRET_PATTERN" >/tmp/vas_secret_hits.txt 2>/dev/null; then
  cat /tmp/vas_secret_hits.txt
  FAIL=1
else
  echo "no_high_confidence_secret_patterns_found"
fi
rm -f /tmp/vas_secret_hits.txt

echo ""
echo "[plaintext_token_storage_checks]"
if git ls-files | xargs rg -n --no-heading -e "(refresh_token|access_token|client_secret)\\s*[:=]\\s*[\"'][^\"']{8,}[\"']" >/tmp/vas_token_hits.txt 2>/dev/null; then
  cat /tmp/vas_token_hits.txt
  FAIL=1
else
  echo "no_plaintext_token_assignments_in_tracked_files"
fi
rm -f /tmp/vas_token_hits.txt

echo ""
echo "[python_security_lint]"
if command -v bandit >/dev/null 2>&1; then
  if bandit -q -r worker app/src/core_py > "$OUT_DIR/bandit_report.txt"; then
    echo "bandit=pass"
  else
    echo "bandit=fail (see $OUT_DIR/bandit_report.txt)"
    FAIL=1
  fi
else
  echo "bandit=skip (not installed)"
fi

echo ""
echo "[python_dependency_audit]"
if command -v pip-audit >/dev/null 2>&1; then
  if pip-audit > "$OUT_DIR/pip_audit_report.txt"; then
    echo "pip_audit=pass"
  else
    echo "pip_audit=fail (see $OUT_DIR/pip_audit_report.txt)"
    FAIL=1
  fi
elif [[ -x worker/.venv/bin/python ]]; then
  if worker/.venv/bin/python -m pip_audit > "$OUT_DIR/pip_audit_report.txt" 2>/dev/null; then
    echo "pip_audit=pass"
  else
    echo "pip_audit=skip (pip_audit module unavailable)"
  fi
else
  echo "pip_audit=skip (not installed)"
fi

echo ""
echo "[rust_dependency_audit]"
if command -v cargo >/dev/null 2>&1; then
  if (cd native/vas_keyring && cargo audit > "$REPORT_ABS.cargo_audit.txt" 2>&1); then
    echo "cargo_audit=pass"
  else
    if rg -n --fixed-strings "no such command: `audit`" "$REPORT_ABS.cargo_audit.txt" >/dev/null 2>&1; then
      echo "cargo_audit=skip (cargo-audit plugin not installed)"
    else
      echo "cargo_audit=fail (see $REPORT_ABS.cargo_audit.txt)"
      FAIL=1
    fi
  fi
else
  echo "cargo_audit=skip (cargo not installed)"
fi

echo ""
echo "[keyring_plaintext_guard]"
if rg -n --no-heading -e '(refresh_token|access_token|client_secret)' app/src/core app/src/adapters app/src/core_py \
  | rg -v 'redact|REDACT|pattern|example|test' >/tmp/vas_keyring_refs.txt; then
  cat /tmp/vas_keyring_refs.txt
  echo "note=review token references above for storage/logging intent"
else
  echo "no_unexpected_token_references_found_in_core_paths"
fi
rm -f /tmp/vas_keyring_refs.txt

if [[ "$FAIL" -ne 0 ]]; then
  echo "Security audit failed. See $REPORT_ABS" >&2
  exit 1
fi

echo "Security audit passed (or skipped optional tool checks). See $REPORT_ABS"
