#!/usr/bin/env bash
set -euo pipefail
DIR="capsule/v1.5"
J="$DIR/hashes.json"

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq not installed. (mac: brew install jq)"; exit 2
fi
if [[ ! -f "$J" ]]; then
  echo "ERROR: missing $J"; exit 1
fi

fail=0

# 1) Every manifest entry exists
while read -r rel; do
  [[ -n "$rel" ]] || continue
  if [[ ! -f "$DIR/$rel" ]]; then
    echo "MISSING: $rel (listed in hashes.json)"
    fail=1
  fi
done < <(jq -r 'keys[]' "$J")

# 2) Hashes match
while read -r name expect; do
  [[ -f "$DIR/$name" ]] || continue
  if command -v shasum >/dev/null 2>&1; then
    have=$(shasum -a 256 "$DIR/$name" | awk '{print $1}')
  else
    have=$(openssl dgst -sha256 "$DIR/$name" | awk '{print $2}')
  fi
  if [[ "$have" != "$expect" ]]; then
    echo "HASH MISMATCH: $name"
    echo "  expect: $expect"
    echo "  have:   $have"
    fail=1
  fi
done < <(jq -r 'to_entries[] | "\(.key) \(.value)"' "$J")

# 3) Warn on unmanifested files under the capsule dir
while read -r base; do
  jq -e --arg b "$base" 'has($b)' "$J" >/dev/null || \
    echo "WARN: Unmanifested file under $DIR: $base"
done < <(find "$DIR" -maxdepth 1 -type f -not -name 'hashes.json' -printf '%f\n' 2>/dev/null)

exit $fail
