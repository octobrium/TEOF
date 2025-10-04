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

agent_id="$(python3 - <<'PY'
import json, pathlib, sys

manifest = pathlib.Path("AGENT_MANIFEST.json")
if not manifest.exists():
    print("preflight: AGENT_MANIFEST.json is missing; run session_boot to activate an agent manifest", file=sys.stderr)
    sys.exit(1)

try:
    data = json.loads(manifest.read_text(encoding="utf-8"))
except Exception as exc:  # pragma: no cover - guard path
    print(f"preflight: cannot parse AGENT_MANIFEST.json ({exc})", file=sys.stderr)
    sys.exit(1)

agent = data.get("agent_id", "").strip()
if not agent:
    print("preflight: agent_id missing in AGENT_MANIFEST.json; update the manifest or rerun session_boot", file=sys.stderr)
    sys.exit(1)

print(agent)
PY
  )"

if [[ -z "$agent_id" ]]; then
  echo "preflight: unable to determine agent_id from AGENT_MANIFEST.json" >&2
  exit 1
fi

tail_receipt="_report/session/${agent_id}/manager-report-tail.txt"
if [[ ! -s "$tail_receipt" ]]; then
  echo "preflight: manager-report tail receipt missing at $tail_receipt" >&2
  echo "  Run 'python3 -m tools.agent.session_boot' to capture the manager-report tail before preflight." >&2
  exit 1
fi

python3 tools/receipts/main.py check
python3 -m tools.maintenance.worktree_guard --max-changes 80
python3 tools/snippets/render_quickstart.py
python3 tools/snippets/check_quickstart_docs.py --apply
git diff --exit-code docs/_generated/quickstart_snippet.md README.md docs/quickstart.md docs/agents.md .github/AGENT_ONBOARDING.md
python3 -m tools.maintenance.plan_hygiene
python3 scripts/ci/check_plans.py
python3 tools/planner/validate.py --strict --output _report/planner/validate/summary-latest.json
python3 tools/agent/bus_status.py --json --limit 5 >/dev/null
pytest tests/test_agent_bus_status.py tests/test_ocers_rules.py tests/test_brief.py tests/test_ocers_eval.py

echo "Preflight complete: receipts, plans, planner validation, bus status, targeted tests verified."
