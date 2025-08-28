#!/usr/bin/env bash
set -euo pipefail

roots=("extensions")
banned=("experimental" "archive" "legacy")

fail=0
for r in "${roots[@]}"; do
  [ -d "$r" ] || continue
  while IFS= read -r -d '' py; do
    for b in "${banned[@]}"; do
      if grep -nE "from[[:space:]]+$b(\.|[[:space:]])|import[[:space:]]+$b(\.|[[:space:]])" "$py" >/dev/null; then
        echo "POLICY FAIL: $py imports from banned namespace '$b'"
        fail=1
      fi
    done
  done < <(find "$r" -type f -name "*.py" -print0)
done
exit $fail
