#!/usr/bin/env bash
# Automated guard that runs before pushing commits.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "pre-push hook requires python3" >&2
  exit 1
fi

if ! command -v pytest >/dev/null 2>&1; then
  echo "pre-push hook requires pytest" >&2
  exit 1
fi

python3 tools/receipts/main.py check
python3 tools/planner/validate.py --strict
pytest tests/test_agent_bus_status.py tests/test_systemic_rules.py tests/test_brief.py tests/test_systemic_eval.py
