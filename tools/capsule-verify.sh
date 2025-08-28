#!/usr/bin/env bash
set -euo pipefail

ver="$(tr -d '\n' < capsule/current)"

if ! jq -e --arg v "$ver" '.tree[$v]' "capsule/$ver/reconstruction.json" >/dev/null 2>&1; then
  echo "::error::capsule/$ver/reconstruction.json missing .tree[\"$ver\"]"; exit 1
fi
expected="$(jq -r --arg v "$ver" '.tree[$v]' "capsule/$ver/reconstruction.json")"

# Build a manifest of content hashes ONLY (no paths) and tree hash it.
manifest_now="$(
  find "capsule/$ver" -type f \
    ! -path "capsule/$ver/reconstruction.json" \
    ! -path "capsule/$ver/hashes.json" \
    ! -path "capsule/$ver/root" \
    ! -path "capsule/$ver/files" \
    ! -path "capsule/$ver/count" \
    ! -name ".DS_Store" \
    -print0 \
  | xargs -0 -I{} sh -c 'sha256sum "{}" | awk "{print \$1}"' \
  | sort
)"
tree_now="$(printf "%s\n" "$manifest_now" | sha256sum | awk '{print $1}')"

if [[ "$tree_now" != "$expected" ]]; then
  echo "::error::Capsule content tree mismatch for $ver"
  echo "expected: $expected"
  echo "actual:   $tree_now"
  exit 1
fi
echo "✓ Capsule content tree OK ($ver)"
