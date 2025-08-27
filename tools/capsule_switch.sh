#!/usr/bin/env bash
set -euo pipefail
V="${1:?usage: tools/capsule_switch.sh vX.Y}"
[ -d "capsule/$V" ] || { echo "capsule/$V not found"; exit 1; }
ln -snf "$V" capsule/current
git add capsule/current
git commit -m "capsule: switch live pointer -> $V" || true
tools/doctor.sh
echo "✓ capsule/current -> $V"
