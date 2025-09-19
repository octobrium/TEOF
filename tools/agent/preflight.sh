#!/usr/bin/env bash
# Preflight checklist for agents before opening a PR.
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

if ! command -v pytest >/dev/null 2>&1; then
  echo "pytest is required" >&2
  exit 1
fi

python3 tools/receipts/main.py check
python3 -m tools.maintenance.plan_hygiene
python3 scripts/ci/check_plans.py
python3 tools/planner/validate.py --strict
python3 tools/agent/bus_status.py --json --limit 5 >/dev/null
pytest tests/test_agent_bus_status.py tests/test_ocers_rules.py tests/test_brief.py tests/test_ocers_eval.py

echo "Preflight complete: receipts, plans, planner validation, bus status, targeted tests verified."
