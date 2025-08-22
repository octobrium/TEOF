#!/usr/bin/env bash
# freeze_hashes.command — refresh capsule hash manifest (macOS-friendly)
# - Writes: seed/capsule/<version>/hashes.json
# - Keys are *relative to the version dir* (e.g., "capsule.txt")
# - Version selection priority:
#     1) --version vX.Y
#     2) seed/capsule/current symlink target
#     3) latest seed/capsule/v*/ (sorted -V)
# - Exits if required canonical files are missing.

set -euo pipefail

# --- locate repo root (supports legacy/scripts/ or scripts/ placement) ---
here="$(cd "$(dirname "$0")" && pwd)"
for probe in "$here" "$here/.." "$here/../.."; do
  if [ -d "$probe/seed/capsule" ]; then
    ROOT="$probe"
    break
  fi
done
if [ -z "${ROOT:-}" ]; then
  echo "ERROR: could not find repo root containing seed/capsule/"
  read -r -p "Press Return to close..." _ || true
  exit 1
fi

CAP_ROOT="$ROOT/seed/capsule"
CUR="$CAP_ROOT/current"

# --- parse optional --version flag ---
VERSION="${1:-}"
if [[ "${VERSION}" == "--version" || "${VERSION}" == "-v" ]]; then
  VERSION="${2:-}"
fi

# --- infer version from symlink if not provided ---
if [[ -z "${VERSION}" && -L "$CUR" ]]; then
  link_target="$(readlink "$CUR" || true)"
  VERSION="${link_target%/}"
fi

# --- fallback: pick latest v*/ if still empty ---
if [[ -z "${VERSION}" ]]; then
  mapfile -t _VERS < <(ls -1d "$CAP_ROOT"/v*/ 2>/dev/null | sed 's#.*/##' | sort -V)
  if (( ${#_VERS[@]} )); then
    VERSION="${_VERS[-1]}"
    echo "No version provided; using latest versioned folder: ${VERSION}"
  fi
fi

if [[ -z "$VERSION" ]]; then
  echo "ERROR: cannot determine version."
  echo "  Either make seed/capsule/current a symlink to vX.Y, or run:"
  echo "  $0 --version vX.Y"
  read -r -p "Press Return to close..." _ || true
  exit 1
fi

BASE="$CAP_ROOT/$VERSION"
OUT="$BASE/hashes.json"

if [[ ! -d "$BASE" ]]; then
  echo "ERROR: $BASE does not exist."
  echo "  Create it (e.g., copy from seed/capsule/current) and try again."
  read -r -p "Press Return to close..." _ || true
  exit 1
fi

# --- canonical sets (relative file names inside $BASE) ---
# Required: must exist; Optional: hashed if present (warn if missing).
required_files=(
  "capsule.txt"
  "capsule-mini.txt"
  "capsule-selfreconstructing.txt"
  "capsule-handshake.txt"
  "reconstruction.json"
  "tests.md"
  "PROVENANCE.md"
)

optional_files=(
  "RELEASE.md"
  "calibration.md"
  "OGS-spec.md"
  "canonical-teof.md"
  "core-teof.md"
  "volatile-data-protocol.md"
  "TEOF-FUTURE.md"
)

# --- verify required files ---
missing=0
for rel in "${required_files[@]}"; do
  if [[ ! -f "$BASE/$rel" ]]; then
    echo "ERROR: missing $BASE/$rel"
    missing=1
  fi
done
if (( missing != 0 )); then
  echo "Aborting due to missing required canonical files."
  read -r -p "Press Return to close..." _ || true
  exit 1
fi

# --- collect files to hash (required + optional-if-present) ---
to_hash=()
for rel in "${required_files[@]}";   do to_hash+=("$rel"); done
for rel in "${optional_files[@]}";  do [[ -f "$BASE/$rel" ]] && to_hash+=("$rel") || echo "warn: optional missing $rel"; done

# --- write hashes.json with relative keys ---
mkdir -p "$BASE"
{
  echo "{"
  for i in "${!to_hash[@]}"; do
    rel="${to_hash[$i]}"
    # macOS shasum prints: "<hash>  <file>"
    hash_val="$(shasum -a 256 "$BASE/$rel" | awk '{print $1}')"
    sep=","
    [[ "$i" == "$(( ${#to_hash[@]} - 1 ))" ]] && sep=""
    printf '  "%s": "%s"%s\n' "$rel" "$hash_val" "$sep"
  done
  echo "}"
} > "$OUT"

echo
echo "Live version  → $VERSION"
echo "Baseline dir  → $BASE"
echo "Manifest      → $OUT"
echo "✔ Done. Next: git add/commit/push the updated hashes.json"
read -r -p "Press Return to close..." _ || true
