#!/usr/bin/env bash
set -euo pipefail

# Compute files changed vs origin/main (fallback: HEAD)
files=()
if git rev-parse --verify origin/main >/dev/null 2>&1; then
  base="$(git merge-base origin/main HEAD)"
  while IFS= read -r -d '' f; do
    files+=("$f")
  done < <(git diff --name-only -z "$base"...HEAD)
else
  while IFS= read -r -d '' f; do
    files+=("$f")
  done < <(git diff --name-only -z HEAD~1..HEAD 2>/dev/null || printf '')
fi

# If nothing changed, we're OK.
if [ ${#files[@]} -eq 0 ]; then
  echo "append-only: OK (no changes)"
  exit 0
fi

# Allowlist of top-level buckets (kept small + canonical)
allowed=(
  .
  _apoptosis
  _bus
  _plans
  _report
  agents
  bin
  capsule
  datasets
  docs
  extensions
  governance
  memory
  pyproject.toml
  queue
  scripts
  teof
  tests
  tools
  .github
  .githooks
  AGENT_MANIFEST.json
  CHANGELOG.md
  CODE_OF_CONDUCT.md
  CONTRIBUTING.md
  LICENSE
  Makefile
  NOTICE
  README.md
  SECURITY.md
  .editorconfig
  .gitattributes
  .gitignore
)

status=0
for f in "${files[@]}"; do
  top="${f%%/*}"
  [ "$top" = "$f" ] && top="."

  allowed_hit=0
  for entry in "${allowed[@]}"; do
    if [ "$entry" = "$top" ]; then
      allowed_hit=1
      break
    fi
  done

  if [ $allowed_hit -eq 0 ]; then
    echo "Unexpected top-level dir: $top"
    status=1
  fi
done

if [ $status -eq 0 ]; then
  echo "append-only: OK (allowed top-level changes)"
else
  exit 1
fi
