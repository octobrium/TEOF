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
python3 -m tools.maintenance.worktree_guard --max-changes 80
python3 tools/snippets/render_quickstart.py
python3 tools/snippets/check_quickstart_docs.py --apply
git diff --exit-code docs/_generated/quickstart_snippet.md README.md docs/quickstart.md docs/AGENTS.md .github/AGENT_ONBOARDING.md
python3 -m tools.maintenance.plan_hygiene
python3 scripts/ci/check_plans.py
python3 tools/planner/validate.py --strict
python3 tools/agent/bus_status.py --json --limit 5 >/dev/null
pytest tests/test_agent_bus_status.py tests/test_ocers_rules.py tests/test_brief.py tests/test_ocers_eval.py

echo "Preflight complete: receipts, plans, planner validation, bus status, targeted tests verified."
