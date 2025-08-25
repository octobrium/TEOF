#!/usr/bin/env bash
set -euo pipefail
staged="$(git diff --cached --name-only || true)"
[ -z "$staged" ] && exit 0
if echo "$staged" | grep -E '\.bak|\.save' >/dev/null 2>&1; then
  echo "pre-commit: refuse to commit *.bak* or *.save files."
  echo "$staged" | grep -E '\.bak|\.save' | sed 's/^/  - /'
  exit 1
fi
exit 0
