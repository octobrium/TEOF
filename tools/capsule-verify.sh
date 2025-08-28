#!/usr/bin/env bash
set -euo pipefail
ver=$(tr -d '\n' < capsule/current)

# recompute content-only tree hash of tracked files
readarray -t hashes < <(git ls-files -z "capsule/$ver" \
  | tr '\0' '\n' | awk 'length>0' \
  | while read -r f; do shasum -a 256 "$f" | awk '{print $1}'; done)
tree_now=$(printf "%s\n" "${hashes[@]}" | LC_ALL=C sort | shasum -a 256 | awk '{print $1}')

expected=$(jq -r --arg v "$ver" '.tree[$v] // empty' "capsule/$ver/reconstruction.json")
if [[ -z "$expected" ]]; then
  echo "::error::No .tree[$ver] in capsule/$ver/reconstruction.json"
  exit 1
fi

if [[ "$expected" != "$tree_now" ]]; then
  echo "::error::Capsule content tree mismatch for $ver
expected: $expected
actual:   $tree_now"
  exit 1
fi

echo "Capsule content tree OK for $ver."
