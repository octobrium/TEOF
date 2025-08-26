#!/usr/bin/env bash
set -euo pipefail
echo "== Capsule hash audit =="
scripts/ci/check_hashes.sh || true
echo
echo "== Append-only audit (HEAD vs origin/main) =="
scripts/ci/check_append_only.sh origin/main || true
