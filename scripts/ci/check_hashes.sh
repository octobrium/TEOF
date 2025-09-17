#!/usr/bin/env bash
set -euo pipefail
# Optional arg may be a capsule path (capsule/vX.Y) or bare version (vX.Y); default uses capsule/current.
TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
  if [[ -f "capsule/current" ]]; then
    TARGET="capsule/$(tr -d '\n' < capsule/current)"
  else
    TARGET="capsule/v1.5"
  fi
elif [[ "$TARGET" != capsule/* ]]; then
  TARGET="capsule/${TARGET}"
fi

DIR="$TARGET"
J="$DIR/hashes.json"

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq not installed. (mac: brew install jq)"; exit 2
fi
if [[ ! -f "$J" ]]; then
  echo "ERROR: missing $J"; exit 1
fi

fail=0

if jq -e '.files and (.files | type == "array")' "$J" >/dev/null 2>&1; then
  # New-format manifest (root name, file count, array of {path, sha256}).
  root_name=$(jq -r '.root // empty' "$J")
  expected_count=$(jq -r '.count // empty' "$J")
  actual_items=$(jq -r '.files | length' "$J")

  if [[ -n "$root_name" ]]; then
    dir_name="$(basename "$DIR")"
    if [[ "$root_name" != "$dir_name" ]]; then
      echo "ROOT MISMATCH: manifest root=$root_name, dir=$dir_name"
      fail=1
    fi
  fi

  if [[ -n "$expected_count" && "$expected_count" != "$actual_items" ]]; then
    echo "COUNT MISMATCH: manifest count=$expected_count, files array has $actual_items entries"
    fail=1
  fi

  manifest_paths=()
  while IFS=' ' read -r rel sha; do
    [[ -n "$rel" ]] || continue
    manifest_paths+=("$rel")
    [[ "$rel" == "hashes.json" ]] && continue
    path="$DIR/$rel"
    if [[ ! -f "$path" ]]; then
      echo "MISSING: $rel (listed in hashes.json)"
      fail=1
      continue
    fi
    if command -v shasum >/dev/null 2>&1; then
      have=$(shasum -a 256 "$path" | awk '{print $1}')
    else
      have=$(openssl dgst -sha256 "$path" | awk '{print $2}')
    fi
    if [[ "$have" != "$sha" ]]; then
      echo "HASH MISMATCH: $rel"
      echo "  expect: $sha"
      echo "  have:   $have"
      fail=1
    fi
  done < <(jq -r '.files[] | select(.path and .sha256) | "\(.path) \(.sha256)"' "$J")

  while read -r base; do
    [[ -n "$base" ]] || continue
    [[ "$base" == "hashes.json" ]] && continue
    found=0
    for rel in "${manifest_paths[@]}"; do
      if [[ "$rel" == "$base" ]]; then
        found=1
        break
      fi
    done
    if [[ $found -eq 0 ]]; then
      echo "WARN: Unmanifested file under $DIR: $base"
    fi
  done < <(find "$DIR" -maxdepth 1 -type f -printf '%f\n' 2>/dev/null)
else
  # Legacy format: flat filename -> sha256 map.
  while read -r rel; do
    [[ -n "$rel" ]] || continue
    if [[ ! -f "$DIR/$rel" ]]; then
      echo "MISSING: $rel (listed in hashes.json)"
      fail=1
    fi
  done < <(jq -r 'keys[]' "$J")

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

  while read -r base; do
    jq -e --arg b "$base" 'has($b)' "$J" >/dev/null || \
      echo "WARN: Unmanifested file under $DIR: $base"
  done < <(find "$DIR" -maxdepth 1 -type f -not -name 'hashes.json' -printf '%f\n' 2>/dev/null)
fi

exit $fail
