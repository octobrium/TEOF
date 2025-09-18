#!/usr/bin/env bash
# Preflight checklist for agents before opening a PR.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

python3 tools/receipts/main.py check
python3 scripts/ci/check_plans.py
python3 tools/agent/bus_status.py --json --limit 5 >/dev/null

echo "Preflight complete: receipts, plans, bus status verified."
