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
