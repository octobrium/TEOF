#!/usr/bin/env sh
set -eu

if [ ! -L "capsule/current" ]; then
  echo "ERROR: capsule/current must be a symlink to the active capsule version"
  exit 1
fi

ver="$(readlink "capsule/current")"
ver="${ver#capsule/}"

if [ -z "$ver" ]; then
  echo "ERROR: capsule/current symlink is empty"
  exit 1
fi

if [ ! -f "capsule/$ver/reconstruction.json" ]; then
  echo "ERROR: capsule/$ver/reconstruction.json is missing (seed the tree first)."
  exit 1
fi

# Current repo manifest for this capsule version (path list, sorted)
manifest_now=$(
  git ls-tree -r --name-only -z HEAD -- "capsule/$ver" \
  | tr -d '\r' | tr '\0' '\n' | LC_ALL=C sort -u
)

# Hash the manifest bytes (content-tree hash)
tree_now=$(printf "%s" "$manifest_now" | shasum -a 256 | awk '{print $1}')

# Expected hash & expected manifest from the seed file
tree_expected=$(jq -r --arg v "$ver" '.tree[$v] // empty' "capsule/$ver/reconstruction.json")
if [ -z "$tree_expected" ]; then
  echo "ERROR: no .tree[\"$ver\"] in capsule/$ver/reconstruction.json"
  exit 1
fi

if [ "$tree_now" = "$tree_expected" ]; then
  echo "Capsule content tree OK for $ver."
  exit 0
fi

# Show helpful diffs
expected_list=$(jq -r --arg v "$ver" '.files[$v][]?' "capsule/$ver/reconstruction.json" | LC_ALL=C sort -u)

t1=$(mktemp); t2=$(mktemp)
printf "%s\n" "$manifest_now"   | LC_ALL=C sort -u > "$t1"
printf "%s\n" "$expected_list"  | LC_ALL=C sort -u > "$t2"

echo "::error::Capsule content tree mismatch for $ver"
echo "expected: $tree_expected"
echo "actual  : $tree_now"
echo
echo "Files only in repo (missing from reconstruction.json):"
comm -23 "$t1" "$t2" || true
echo
echo "Files only in reconstruction.json (missing from repo):"
comm -13 "$t1" "$t2" || true

rm -f "$t1" "$t2"
exit 2
