#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

OWNER_REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
DEFAULT_BRANCH="$(gh repo view --json defaultBranchRef --jq .defaultBranchRef.name)"

CHECKS=(
  "quality-gates / quality"
  "quality-gates / pinned-toolchain-smoke"
  "quality-gates / v2-train1-acceptance"
  "git-hygiene / commitlint"
  "git-hygiene / pr-title"
  "git-hygiene / branch-name"
  "git-hygiene / secrets"
  "dependency-review / dependency-review"
  "Analyze (python)"
  "Analyze (javascript-typescript)"
)

PAYLOAD_FILE="$(mktemp)"
python3 - <<'PY' "$PAYLOAD_FILE" "${CHECKS[@]}"
import json, sys
out = sys.argv[1]
checks = sys.argv[2:]
payload = {
    "required_status_checks": {
        "strict": True,
        "contexts": checks,
    },
    "enforce_admins": False,
    "required_pull_request_reviews": {
        "dismiss_stale_reviews": True,
        "require_code_owner_reviews": True,
        "required_approving_review_count": 1,
    },
    "restrictions": None,
    "required_conversation_resolution": True,
    "allow_force_pushes": False,
    "allow_deletions": False,
    "required_linear_history": True,
}
with open(out, "w", encoding="utf-8") as f:
    json.dump(payload, f)
PY

set +e
RESP="$(gh api -X PUT "repos/$OWNER_REPO/branches/$DEFAULT_BRANCH/protection" --input "$PAYLOAD_FILE" 2>&1)"
RC=$?
set -e
rm -f "$PAYLOAD_FILE"

if [[ $RC -ne 0 ]]; then
  if echo "$RESP" | grep -q "Upgrade to GitHub Pro or make this repository public"; then
    echo "Branch protection unavailable on current repo tier; local/CI guardrails remain active."
    echo "$RESP"
    exit 0
  fi
  echo "$RESP" >&2
  exit $RC
fi

echo "Branch protection configured on $OWNER_REPO:$DEFAULT_BRANCH"
