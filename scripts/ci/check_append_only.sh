#!/usr/bin/env bash
set -euo pipefail

# files that must be append-only (tune this list if needed)
PATTERNS=(
  "capsule/v1.5/*.md"
  "capsule/v1.5/capsule.txt"
  "capsule/v1.5/capsule-handshake.txt"
)

BASE=${1:-"origin/main"}
if ! git rev-parse -q --verify "$BASE" >/dev/null 2>&1; then
  BASE="$(git rev-parse HEAD^ 2>/dev/null || echo HEAD~1)"
fi

fail=0
for pat in "${PATTERNS[@]}"; do
  while IFS= read -r f; do
    [[ -n "$f" ]] || continue
    # diff (no context). flag any deleted content lines (exclude headers)
    if git diff -U0 "$BASE"...HEAD -- "$f" | grep -E '^-[^-\+@]' >/dev/null; then
      echo "APPEND-ONLY VIOLATION: $f (contains deletions or non-append edits)"
      fail=1
    fi
  done < <(git diff --name-only "$BASE"...HEAD -- $pat || true)
done

exit $fail
