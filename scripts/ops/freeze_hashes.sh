#!/usr/bin/env bash
set -euo pipefail

VER=""
if [ "${1:-}" = "--version" ]; then VER="${2:-}"; shift 2; fi
if [ -z "${VER:-}" ] && [ -L capsule/current ]; then VER="$(basename "$(readlink capsule/current)")"; fi
if [ -z "${VER:-}" ]; then VER="$(basename "$(ls -d capsule/v*/ 2>/dev/null | head -n 1)" | tr -d '/')"; fi
[ -n "${VER:-}" ] || { echo "ERROR: cannot determine version"; exit 1; }

CAPS="capsule/$VER"
[ -d "$CAPS" ] || { echo "ERROR: $CAPS missing"; exit 1; }

hash_cmd() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}';
  elif command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}';
  else openssl dgst -sha256 "$1" | awk '{print $2}'; fi
}

tmp="$(mktemp)"
{
  echo "{"
  first=1
  while IFS= read -r f; do
    base="$(basename "$f")"
    h="$(hash_cmd "$f")"
    if [ $first -eq 1 ]; then first=0; sep=""; else sep=","; fi
    printf '%s\n  "%s": "%s"' "$sep" "$base" "$h"
  done < <(find "$CAPS" -maxdepth 1 -type f -print | sort)
  echo ""
  echo "}"
} > "$tmp"

mv "$tmp" hashes.json
echo "Wrote hashes.json for $VER"
