#!/usr/bin/env bash
set -euo pipefail
echo "🤝  Autocollab (dry-run) — queue → _report/autocollab/<ts>"
scripts/bot/autocollab.py
echo "📦  See _report/autocollab for proposals + OCERS stub scores"
