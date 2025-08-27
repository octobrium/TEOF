#!/usr/bin/env bash
set -euo pipefail

# Pick version
pick_next() {
  ls -1 capsule 2>/dev/null | grep -E '^v[0-9]+(\.[0-9]+)?$' | sort -V | tail -n1 | awk -F. '
    /^v[0-9]+(\.[0-9]+)?$/ {
      if (NF==1){ print $0".1"; exit }
      sub(/^v/,"",$1); print "v"$1"."$2+1
    }'
}
V="${V:-}"
if [ -z "${V}" ]; then
  V="$(pick_next || true)"
  [ -n "$V" ] || V="v1.1"
fi

SRC="capsule/${V}"
# If target dir doesn't exist, initialize it from current symlink target (read-only copy)
if [ ! -d "$SRC" ]; then
  if [ -L capsule/current ]; then
    tgt="$(readlink capsule/current)"
    [ -d "capsule/$tgt" ] || { echo "capsule/$tgt missing"; exit 1; }
    mkdir -p "$SRC"
    rsync -a --exclude 'hashes.json' "capsule/$tgt/"/ "$SRC"/
    echo "→ seeded $SRC from $tgt"
  else
    echo "no capsule/current symlink; create capsule/$V manually"; exit 1
  fi
fi

# Build deterministic hashes.json
python3 scripts/ci/make_hashes.py "$SRC" > "$SRC/hashes.json"
echo "→ wrote $SRC/hashes.json"

# Prepare anchors event stub (do not append; write to _report)
# prev_content_hash = SHA-256(HEAD:governance/anchors.json)
HEAD_HASH="$(git show HEAD:governance/anchors.json 2>/dev/null | shasum -a 256 | awk '{print $1}')"
[ -z "${HEAD_HASH}" ] && HEAD_HASH="$(python3 - <<'PY'
import sys,hashlib,subprocess
try:
    b = subprocess.check_output(["git","show","HEAD:governance/anchors.json"])
    print(hashlib.sha256(b).hexdigest())
except Exception:
    print("")
PY
)"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p _report/anchors
cat > "_report/anchors/new_event.${V}.json" <<EOF
{
  "ts": "${TS}",
  "type": "capsule_freeze",
  "version": "${V}",
  "prev_content_hash": "${HEAD_HASH}",
  "notes": "freeze ${V}; hashes.json updated deterministically; manual append required"
}
EOF
echo "→ wrote _report/anchors/new_event.${V}.json (manual append required)"

echo "✓ Freeze prepared. Next steps:"
echo "  1) Review ${SRC}/hashes.json"
echo "  2) Manually append _report/anchors/new_event.${V}.json to governance/anchors.json (end of file)"
echo "  3) Optionally switch:  ln -snf ${V} capsule/current  (then commit)"
