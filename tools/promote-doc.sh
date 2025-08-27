#!/usr/bin/env bash
set -euo pipefail
# Optional: set RUN_PULSE=1 to refresh batch before promoting
if [ "${RUN_PULSE:-0}" = "1" ]; then
  [ -x tools/pulse.sh ] && tools/pulse.sh || true
fi

# Ensure we have a selection
[ -x tools/select.sh ] && tools/select.sh >/dev/null || true

# Pick top index
IDX="$(python3 scripts/bot/pick_top.py || true)"
if [ -z "$IDX" ]; then
  echo "No candidate available. Run tools/pulse.sh first, then tools/select.sh."; exit 0
fi

echo "→ Promoting item index: $IDX"
# Accept → ledger → create docs draft branch
[ -x tools/accept.sh ] && tools/accept.sh "$IDX" || true
[ -x tools/ledger.sh ] && tools/ledger.sh || true
[ -x tools/doc-autopr.sh ] && tools/doc-autopr.sh || true

echo "✓ Promotion done. Review branch printed above (from doc-autopr)."
echo "  Next: git push -u origin <branch>; open PR (or dispatch the workflow)."
