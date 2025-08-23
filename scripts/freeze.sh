#!/usr/bin/env bash
# freeze.sh — refresh capsule/<version>/hashes.json (or capsule/current by default)
set -euo pipefail

usage() {
  echo "Usage: $(basename "$0") [--version vX.Y]"
  exit 2
}

VERSION=""
if [[ "${1:-}" == "--version" && -n "${2:-}" ]]; then
  VERSION="$2"; shift 2
fi

BASE="capsule/current"
if [[ -n "$VERSION" ]]; then
  BASE="capsule/$VERSION"
fi

# Resolve BASE (accept symlink or directory)
if [[ ! -d "$BASE" ]]; then
  echo "ERROR: capsule dir not found: $BASE" >&2
  exit 1
fi

HASHES_JSON="$BASE/hashes.json"
TMP="$(mktemp)"

# Portable sha256 helper
sha256() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    sha256sum "$1" | awk '{print $1}'
  fi
}

# Build a sorted list of file paths relative to BASE, excluding hashes.json itself
mapfile -d '' FILES < <(cd "$BASE" && find . -type f -not -name 'hashes.json' -print0 | sort -z)

{
  echo "{"
  for ((i=0; i<${#FILES[@]}; i++)); do
    rel="${FILES[$i]#./}"
    abs="$BASE/$rel"
    h="$(sha256 "$abs")"
    comma=","
    [[ "$i" -eq $((${#FILES[@]}-1)) ]] && comma=""
    printf '  "%s": "%s"%s\n' "$rel" "$h" "$comma"
  done
  echo "}"
} > "$TMP"

mkdir -p "$(dirname "$HASHES_JSON")"
mv -f "$TMP" "$HASHES_JSON"

# Optional: append a light anchors event
ANCHORS="governance/anchors.json"
python3 - <<'PY'
import json, datetime, os, sys
p="governance/anchors.json"
os.makedirs(os.path.dirname(p), exist_ok=True)
try:
    with open(p,"r",encoding="utf-8") as f: data=json.load(f)
except FileNotFoundError:
    data={"events":[]}
data.setdefault("events",[]).append({
  "type":"freeze",
  "ts": datetime.datetime.utcnow().isoformat(timespec="seconds")+"Z",
})
with open(p,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
print("anchors updated:", p)
PY

echo "Refreshed $HASHES_JSON"
