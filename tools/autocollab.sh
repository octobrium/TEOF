#!/usr/bin/env bash
set -euo pipefail
echo "🤝  Autocollab (dry-run) — queue → _report/autocollab/<ts>"
scripts/bot/autocollab.py
echo "📦  See _report/autocollab for proposals + OCERS stub scores"

if [ -x "tools/ledger.sh" ]; then
  echo "📈  Updating ledger with latest batch..."
  if tools/ledger.sh; then
    echo "✅  Ledger updated."
  else
    echo "⚠️  Ledger update failed; run tools/ledger.sh manually." >&2
  fi
fi
