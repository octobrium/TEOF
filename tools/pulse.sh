#!/usr/bin/env bash
set -euo pipefail
echo "🩺  doctor..."
tools/doctor.sh
echo "🤝  autocollab..."
tools/autocollab.sh
echo "🧠  critic..."
tools/critic.sh
echo "📈  ledger..."
tools/ledger.sh
echo "✅  pulse complete."

echo "🧮  selector (suggest-only)..."
tools/select.sh || true

echo "🚀  promote top docs-only suggestion (suggest-only, manual review)..."
echo "     tools/promote-doc.sh    # or set RUN_PULSE=1 to refresh before promoting"
