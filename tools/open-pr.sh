#!/usr/bin/env bash
set -euo pipefail
branch="${1:?branch name}"; label="${2:-}"
# Transform origin to https for browser fallback
remote="$(git remote get-url origin 2>/dev/null || true)"
if [[ "$remote" =~ ^git@([^:]+):(.+)\.git$ ]]; then
  base="https://${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
elif [[ "$remote" =~ ^https?:// ]]; then
  base="${remote%.git}"
else
  echo "Could not parse origin remote; please open PR manually."; exit 0
fi

if command -v gh >/dev/null 2>&1; then
  # Create or reuse PR
  url="$(gh pr create --base main --head "$branch" --title "$branch" --body "Auto-opened by helper" 2>/dev/null || true)"
  # If PR already exists, gh prints error; try to fetch URL
  url="${url:-$(gh pr view --json url -q .url 2>/dev/null || true)}"
  [ -n "${label}" ] && gh pr edit --add-label "$label" >/dev/null 2>&1 || true
  echo "PR: ${url:-<unknown>}"
else
  echo "No gh CLI; open in browser:"
  echo "  ${base}/compare/main...${branch}?expand=1"
  [ -n "$label" ] && echo "Then add label: $label"
fi
