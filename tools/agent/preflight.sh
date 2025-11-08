#!/usr/bin/env bash
# Preflight checklist for agents before opening a PR.
set -euo pipefail

MODE="${1:-core}"
case "$MODE" in
  core|full) ;;
  -h|--help)
    echo "Usage: tools/agent/preflight.sh [core|full]"
    echo "  core (default) → minimal observation guards (tier: core)"
    echo "  full → legacy workflow guard bundle (tier: operational)"
    exit 0
    ;;
  *)
    echo "Unknown mode '$MODE' (expected 'core' or 'full')" >&2
    exit 2
    ;;
esac

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

if [[ "$MODE" == "full" ]] && ! command -v pytest >/dev/null 2>&1; then
  echo "pytest is required for full preflight" >&2
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

dna_targets=("docs/architecture.md" "docs/workflow.md" "docs/promotion-policy.md")
dna_dirty=()
for target in "${dna_targets[@]}"; do
  status_output="$(git status --short -- "$target" 2>/dev/null || true)"
  if [[ -n "$status_output" ]]; then
    dna_dirty+=("$target")
  fi
done

if [[ "${#dna_dirty[@]}" -gt 0 ]]; then
  echo "preflight: DNA docs changed (${dna_dirty[*]}). Verifying memory observation receipt..."
  python3 -m tools.agent.session_guard verify-memory-check --agent "$agent_id" --context dna
fi

log_preflight() {
  local mode="$1"
  local ts
  ts="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  local dir="_report/usage/preflight"
  mkdir -p "$dir"
  cat > "${dir}/preflight-${ts}-${mode}.json" <<EOF
{
  "ts": "${ts}",
  "agent_id": "${agent_id}",
  "mode": "${mode}"
}
EOF
}

if [[ "$MODE" == "core" ]]; then
  log_preflight "core"
  echo "Core preflight complete: observation receipts verified. Run 'tools/agent/preflight.sh full' for workflow guards."
  exit 0
fi

python3 -m tools.maintenance.worktree_guard --max-changes 80
python3 tools/snippets/render_quickstart.py
python3 tools/snippets/check_quickstart_docs.py --apply
git diff --exit-code docs/_generated/quickstart_snippet.md README.md docs/quickstart.md docs/agents.md .github/AGENT_ONBOARDING.md

status_snapshot="$(git status --short)"
onboarding_docs=("docs/onboarding/README.md" "docs/onboarding/tier1-evaluate-PROTOTYPE.md" "docs/onboarding/tier2-solo-dev-PROTOTYPE.md")
onboarding_dirty=()
for doc in "${onboarding_docs[@]}"; do
  if grep -F -- " $doc" <<< "$status_snapshot" >/dev/null; then
    onboarding_dirty+=("$doc")
  fi
done

if [[ "${#onboarding_dirty[@]}" -gt 0 ]]; then
  if ! grep -F -- "doc-verification" <<< "$status_snapshot" >/dev/null; then
    echo "preflight: onboarding docs changed (${onboarding_dirty[*]}) but no doc verification receipts staged (_report/agent/*/doc-verification/…)." >&2
    echo "  Run the SOP in docs/onboarding/doc-verification-sop.md and add the generated receipt before continuing." >&2
    exit 1
  fi
fi

python3 -m tools.maintenance.plan_hygiene
python3 scripts/ci/check_plans.py
python3 tools/planner/validate.py --strict --output _report/planner/validate/summary-latest.json
python3 -m tools.agent.autonomy_status --json
python3 -m tools.autonomy.systemic_radar --markdown docs/reports/systemic-radar.md
python3 scripts/ci/check_systemic_radar.py
python3 tools/agent/bus_status.py --json --limit 5 >/dev/null
pytest tests/test_agent_bus_status.py tests/test_systemic_rules.py tests/test_brief.py tests/test_systemic_eval.py

log_preflight "full"
echo "Full preflight complete: receipts, plans, planner validation, bus status, targeted tests verified."
