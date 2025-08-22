#!/usr/bin/env bash
# freeze_hashes.command — refresh seed/capsule/<ver>/hashes.json
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
# script lives in legacy/scripts/, repo root is two levels up
cd "$here/../.."  # repo root

usage() {
  echo "Usage: $(basename "$0") [--version vX.Y]"
  exit 2
}

ver=""
if [[ "${1:-}" == "--version" && -n "${2:-}" ]]; then
  ver="$2"; shift 2
elif [[ -L seed/capsule/current ]]; then
  # follow the symlink (e.g., v1.5)
  ver="$(readlink seed/capsule/current)"
fi
[[ -n "$ver" ]] || { echo "ERROR: cannot determine version. Use --version vX.Y or create seed/capsule/current -> vX.Y"; read -r -p "Press Return to close..." _; exit 1; }

base="seed/capsule/$ver"
[[ -d "$base" ]] || { echo "ERROR: $base not found"; read -r -p "Press Return to close..." _; exit 1; }

# Canonical set (keys are relative to $base)
paths=(
  "PROVENANCE.md"
  "RELEASE.md"
  "calibration.md"
  "capsule-handshake.txt"
  "capsule-mini.txt"
  "capsule-selfreconstructing.txt"
  "capsule.txt"
  "reconstruction.json"
  "tests.md"
  # normative docs now inside the capsule
  "OGS-spec.md"
  "canonical-teof.md"
  "core-teof.md"
  "volatile-data-protocol.md"
  "TEOF-FUTURE.md"
)

# Verify presence
missing=0
for p in "${paths[@]}"; do
  if [[ ! -f "$base/$p" ]]; then
    echo "ERROR: missing $base/$p"; missing=1
  fi
done
if [[ $missing -ne 0 ]]; then
  echo "Aborting due to missing files."
  read -r -p "Press Return to close..." _; exit 1
fi

out="$base/hashes.json"
tmp="$out.tmp"

# Write hashes atomically
{
  echo "{"
  for i in "${!paths[@]}"; do
    p="${paths[$i]}"
    h="$(shasum -a 256 "$base/$p" | awk '{print $1}')"
    comma=","
    [[ "$i" -eq $((${#paths[@]}-1)) ]] && comma=""
    printf '  "%s": "%s"%s\n' "$p" "$h" "$comma"
  done
  echo "}"
} > "$tmp"

mv -f "$tmp" "$out"

echo "Live version  → $ver"
echo "Baseline file → $out"
echo "✔ Done. Next: commit and push the updated hashes."
read -r -p "Press Return to close..." _ || true
