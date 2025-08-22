#!/bin/bash
# Double-clickable hash refresher for macOS

set -euo pipefail
cd "$(dirname "$0")/.." || exit 1  # Go to repo root (assumes scripts/ location)

# Require stable entrypoint
if [ ! -L "capsule/current" ]; then
  echo "ERROR: capsule/current is not a symlink (expected -> vX.Y)."
  read -r -p "Press Return to close..." _
  exit 1
fi

live="$(readlink "capsule/current")"
if [ -z "$live" ]; then
  echo "ERROR: could not read symlink target."
  read -r -p "Press Return to close..." _
  exit 1
fi

out="capsule/${live}/hashes.json"
mkdir -p "capsule/${live}"

# Canonical immutable set (versionless)
paths=(
  "capsule/current/PROVENANCE.md"
  "capsule/current/capsule-handshake.txt"
  "capsule/current/capsule-mini.txt"
  "capsule/current/capsule-selfreconstructing.txt"
  "capsule/current/capsule.txt"
  "capsule/current/reconstruction.json"
  "capsule/current/tests.md"
)

# Verify presence
missing=0
for p in "${paths[@]}"; do
  if [ ! -f "$p" ]; then
    echo "ERROR: missing $p"
    missing=1
  fi
done
if [ $missing -ne 0 ]; then
  echo "Aborting due to missing files."
  read -r -p "Press Return to close..." _
  exit 1
fi

# Write hashes.json
count=${#paths[@]}
{
  echo "{"
  for ((i=0; i<count; i++)); do
    p="${paths[$i]}"
    h=$(shasum -a 256 "$p" | awk '{print $1}')
    if [ $i -lt $((count-1)) ]; then
      echo "  \"$p\": \"$h\","
    else
      echo "  \"$p\": \"$h\""
    fi
  done
  echo "}"
} > "$out"

echo "Live version  → $live"
echo "Baseline file → $out"
echo "✔ Done. Next: commit and push the updated hashes."
read -r -p "Press Return to close..." _
