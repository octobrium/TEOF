#!/usr/bin/env bash
set -euo pipefail

# Run from the script's directory
cd "$(dirname "$0")"

# Require capsule/current to be a symlink (your stable entrypoint)
if [ ! -L capsule/current ]; then
  echo "ERROR: capsule/current is not a symlink. Point it to your live version (e.g., v1.5) then re-run."
  exit 1
fi

# Detect live version (e.g., v1.5) from the symlink target
live="$(readlink capsule/current)"
if [ -z "${live:-}" ]; then
  echo "ERROR: unable to read symlink target for capsule/current"
  exit 1
fi

out="capsule/${live}/hashes.json"
mkdir -p "capsule/${live}"

echo "Live version → ${live}"
echo "Writing baseline → ${out}"

# Pull immutable paths from anchors/immutable.json (capsule/current/* only)
# This avoids hardcoding and stays aligned with your scope.
mapfile -t paths < <(grep -o '"capsule/current/[^"]*"' anchors/immutable.json | tr -d '"' | sort)

# Fallback if grep finds nothing (shouldn't happen)
if [ ${#paths[@]} -eq 0 ]; then
  echo "WARN: could not extract paths from anchors/immutable.json; using minimal default list."
  paths=(
    "capsule/current/PROVENANCE.md"
    "capsule/current/capsule-handshake.txt"
    "capsule/current/capsule-mini.txt"
    "capsule/current/capsule-selfreconstructing.txt"
    "capsule/current/capsule.txt"
    "capsule/current/reconstruction.json"
    "capsule/current/tests.md"
  )
fi

# Verify all files exist
missing=0
for p in "${paths[@]}"; do
  if [ ! -f "$p" ]; then
    echo "ERROR: missing $p"
    missing=1
  fi
done
if [ "$missing" -ne 0 ]; then
  echo "Aborting due to missing files."
  exit 1
fi

# Write hashes.json
{
  pr
