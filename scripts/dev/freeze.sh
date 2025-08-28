#!/usr/bin/env bash
# freeze.sh — refresh capsule/<version>/hashes.json (or capsule/current by default)
# Compatible with zsh/bash; delegates walking+hashing to Python (no mapfile).
set -euo pipefail

usage() { echo "Usage: $(basename "$0") [--version vX.Y]" >&2; exit 2; }

VERSION=""
if [ "${1-}" = "--version" ] && [ -n "${2-}" ]; then
  VERSION="$2"; shift 2
fi

BASE="capsule/current"
[ -n "${VERSION}" ] && BASE="capsule/${VERSION}"
[ -d "${BASE}" ] || { echo "ERROR: capsule dir not found: ${BASE}" >&2; exit 1; }

# Pass BASE as argv[1] to Python
python3 - "${BASE}" <<'PY'
import hashlib, json, os, sys, datetime

base = sys.argv[1] if len(sys.argv) > 1 else None
if not base:
    print("freeze.sh: BASE not provided", file=sys.stderr)
    sys.exit(2)

hashes = {}
for dirpath, _dirs, files in os.walk(base):
    for name in files:
        if name == "hashes.json":
            continue
        path = os.path.join(dirpath, name)
        rel = os.path.relpath(path, base).replace("\\", "/")
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024*1024), b""):
                h.update(chunk)
        hashes[rel] = h.hexdigest()

out = os.path.join(base, "hashes.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump({k: hashes[k] for k in sorted(hashes)}, f, indent=2, ensure_ascii=False)

# Append a lightweight anchors event
anchors = "governance/anchors.json"
try:
    with open(anchors, "r", encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    data = {"events": []}
data.setdefault("events", []).append({
    "type": "freeze",
    "ts": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
})
os.makedirs(os.path.dirname(anchors), exist_ok=True)
with open(anchors, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Refreshed {out} and appended anchors event.")
PY
