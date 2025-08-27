#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BROOT="$ROOT/_report/autocollab"
[ -d "$BROOT" ] || { echo "no batches yet"; exit 1; }

latest="$(ls -1 "$BROOT" | sort | tail -n1)"
idir="$BROOT/$latest"
idx="${1:-}"
[ -n "$idx" ] || { echo "usage: tools/accept.sh <item-number>"; exit 1; }

itemdir=$(printf "%s/item-%02d" "$idir" "$idx")
[ -d "$itemdir" ] || { echo "missing $itemdir"; exit 1; }

echo '{"accepted": true}' > "$itemdir/accepted.json"
echo "✓ accepted: $latest item-$idx"
