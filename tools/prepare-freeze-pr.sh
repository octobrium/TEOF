#!/usr/bin/env bash
set -euo pipefail
V="${V:?set V, e.g. V=v1.6}"
[ -f "capsule/$V/hashes.json" ] || { echo "capsule/$V/hashes.json not found. Run tools/capsule_freeze.sh first."; exit 1; }
branch="freeze/${V}"
git checkout -b "$branch" 2>/dev/null || git checkout "$branch"
git add "capsule/${V}/hashes.json"
git commit -m "capsule: freeze ${V} (deterministic hashes.json)" || true
git push -u origin "$branch"
echo "✓ Pushed $branch"
echo "Open a PR on GitHub; CI (teof-freeze-verify) will validate determinism."
