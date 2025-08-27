#!/usr/bin/env bash
set -euo pipefail

echo "== verify capsule switch =="
git fetch origin main --quiet
BASE="$(git merge-base HEAD origin/main)"
CHANGED="$(git diff --name-only "$BASE"...HEAD)"
echo "Changed paths:"; echo "$CHANGED" | sed 's/^/  - /'

# Exactly one file changed and it must be capsule/current
if [ "$(echo "$CHANGED" | wc -l | tr -d ' ')" != "1" ] || [ "$CHANGED" != "capsule/current" ]; then
  echo "ERROR: switch PR must change only 'capsule/current'."; exit 1
fi

# Read target version from the file or symlink
TARGET="$( (readlink capsule/current || cat capsule/current) 2>/dev/null | tr -d '\n' )"
echo "capsule/current -> ${TARGET}"
[[ "$TARGET" =~ ^v[0-9]+\.[0-9]+$ ]] || { echo "ERROR: target must look like vN.N"; exit 1; }

# Must exist and contain hashes.json (freeze artifact)
[ -f "capsule/${TARGET}/hashes.json" ] || { echo "ERROR: capsule/${TARGET}/hashes.json missing"; exit 1; }

# Invariants quick pass
tools/doctor.sh

echo "OK: capsule switch verified."
