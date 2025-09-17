#!/usr/bin/env bash
set -euo pipefail

# Compute files changed vs origin/main (fallback: HEAD)
if git rev-parse --verify origin/main >/dev/null 2>&1; then
  base="$(git merge-base origin/main HEAD)"
  files="$(git diff --name-only "$base"...HEAD)"
else
  files="$(git diff --name-only HEAD~1..HEAD 2>/dev/null || true)"
fi

# If nothing changed, we're OK.
[ -n "${files:-}" ] || { echo "append-only: OK (no changes)"; exit 0; }

# Allowlist of top-level buckets (add 'queue')
allowed=". capsule docs governance tools scripts extensions cli teof .github queue memory"

status=0
# shellcheck disable=SC2086
for f in $files; do
  top="${f%%/*}"
  [ "$top" = "$f" ] && top="."
  case " $allowed " in
    *" $top "*) : ;;
    *) echo "Unexpected top-level dir: $top"; status=1 ;;
  esac
done

if [ $status -eq 0 ]; then
  echo "append-only: OK (allowed top-level changes)"
else
  exit 1
fi
