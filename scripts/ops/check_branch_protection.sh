#!/usr/bin/env bash
set -euo pipefail
OWNER="${OWNER:-octobrium}"
REPO="${REPO:-TEOF}"
BRANCH="${BRANCH:-main}"

if ! command -v gh >/dev/null 2>&1; then
  echo "gh not installed (skipping)"
  exit 0
fi

resp="$(gh api "repos/$OWNER/$REPO/branches/$BRANCH/protection/required_status_checks" \
        -H "Accept: application/vnd.github+json" 2>/dev/null || true)"

if [[ -n "${resp:-}" ]]; then
  # Print contexts + strict safely even if fields are missing
  python3 - <<'PY' <<<"$resp" 2>/dev/null || true
import sys, json
try:
    d = json.load(sys.stdin)
    print("contexts:", d.get("contexts"))
    print("strict:", d.get("strict"))
except Exception:
    print("(could not parse required_status_checks JSON; skipping)")
PY
else
  echo "(no required_status_checks found or insufficient perms) – OK for local"
fi
