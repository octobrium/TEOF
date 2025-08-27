#!/usr/bin/env bash
set -euo pipefail
MIN_SCORE="${MIN_SCORE:-7}"
MAX_RISK="${MAX_RISK:-0.40}"
MAX_ITEMS="${MAX_ITEMS:-3}"
REQUIRE_ACCEPTED="${REQUIRE_ACCEPTED:-1}"

python3 scripts/bot/doc_autopr.py

# If drafts were created, stage and commit on a short-lived branch
if git status --porcelain | grep -q '^ M docs/proposals/\|^?? docs/proposals/'; then
  ts="$(date -u +%Y%m%dT%H%M%SZ)"
  branch="autoprops/${ts}"
  git checkout -b "$branch" 2>/dev/null || git checkout "$branch"
  git add docs/proposals/
  git commit -m "docs: import accepted low-risk proposals (auto-draft ${ts})" || true
  echo "→ Created commit on branch: $branch"
  echo "Next: git push -u origin $branch  # then open PR"
else
  echo "No drafts created or nothing to commit."
fi
