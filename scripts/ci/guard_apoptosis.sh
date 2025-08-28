#!/usr/bin/env bash
set -euo pipefail
fail(){ echo "❌ $*"; exit 1; }

# Canonical extensions/ must exist at repo root
[ -d extensions ] || fail "missing top-level 'extensions/'"

# Forbid duplicate 'extensions/' trees OUTSIDE the archive/report areas
dupes=$(git ls-files \
  | grep -E '/extensions/' \
  | grep -vE '^(extensions/|_apoptosis/|_report/)' || true)
[ -z "$dupes" ] || fail "found secondary 'extensions/' trees outside canon:\n$dupes"

# Require expected scripts buckets
for d in scripts scripts/ci scripts/dev scripts/ops; do
  [ -d "$d" ] || fail "missing directory: $d"
done

# Require capsule symlink + freeze artifacts
[ -L capsule/current ] || fail "capsule/current must be a symlink"
ver="$(readlink capsule/current || true)"; [ -n "$ver" ] || fail "capsule/current is empty"
for f in count files root; do [ -f "capsule/$ver/$f" ] || fail "missing capsule/$ver/$f"; done

echo "✅ apoptosis guard OK"
