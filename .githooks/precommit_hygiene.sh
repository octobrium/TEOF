#!/usr/bin/env bash
set -euo pipefail

staged="$(git diff --cached --name-only || true)"
staged_filtered="$(printf '%s\n' "$staged" | grep -v '^archive/' || true)"
[ -z "$staged_filtered" ] && exit 0

if printf '%s\n' "$staged_filtered" | grep -E '\.bak|\.save' >/dev/null 2>&1; then
  echo "pre-commit: refuse to commit *.bak* or *.save files (outside archive/)." >&2
  printf '%s\n' "$staged_filtered" | grep -E '\.bak|\.save' >&2 || true
  exit 1
fi

if printf '%s\n' "$staged_filtered" | grep -E '^experimental/packages/ocers(/|$)' >/dev/null 2>&1; then
  echo "pre-commit: experimental/packages/ocers present; promote or archive first." >&2
  exit 1
fi

for f in capsule/v1.5/capsule-mini.txt capsule/v1.5/capsule-selfreconstructing.txt; do
  if printf '%s\n' "$staged_filtered" | grep -Fx "$f" >/dev/null 2>&1; then
    echo "pre-commit: remove capsule duplicate: $f" >&2
    exit 1
  fi
done
