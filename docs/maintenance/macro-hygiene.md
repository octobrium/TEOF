# Macro Hygiene Objectives — 2025-09-18

Macro hygiene now lives in a structured ledger at `docs/maintenance/macro-hygiene.objectives.json`. The ledger feeds automation so coordination dashboards can confirm each objective stays satisfied.

## Objectives

| id | title | summary | automation signals |
| --- | --- | --- | --- |
| `MH-ENV` | Stabilize environment hygiene | Manifest/branch swap helper keeps AGENT_MANIFEST.json and branches clean between sessions. | `_plans/2025-09-18-manifest-helper-codex3.plan.json`, `_plans/2025-09-19-manifest-swap.plan.json`, `tools/agent/manifest_helper.py`, `tests/test_manifest_helper.py`, `.github/AGENT_ONBOARDING.md` |
| `MH-CI` | Integrate helpers into CI | Prune helper, consensus tooling, and manager heartbeat enforcement live in guardrails workflows. | `_plans/2025-09-18-prune-script.plan.json`, `_plans/2025-09-18-manager-heartbeat.plan.json`, `scripts/ci/check_consensus_receipts.py`, `scripts/ci/consensus_smoke.sh`, `scripts/ci/check_capsule_cadence.py`, `.github/workflows/guardrails.yml`, `tests/test_ci_check_consensus_receipts.py`, `tests/test_ci_check_capsule_cadence.py`, `tests/test_agent_bus_status.py` |
| `MH-CADENCE` | Align capsule cadence | Capsule cadence summary binds releases to consensus receipts and emergent principles. | `_plans/2025-09-21-capsule-cadence-automation.plan.json`, `_report/capsule/summary-latest.json`, `docs/maintenance/capsule-cadence.md`, `tools/capsule/cadence.py`, `governance/core/emergent-principles.jsonl` |
| `MH-AUTO` | Clarify auto-progression triggers | Auto-consent policy, unattended loop receipts, and docs explain when agents may proceed. | `_plans/2025-09-23-autonomy-auto-proceed.plan.json`, `docs/automation/autonomy-consent.json`, `docs/automation.md`, `tools/autonomy/next_step.py`, `tests/test_autonomy_next_step.py` |

## Automation

- `python -m tools.autonomy.macro_hygiene` emits the objective status and writes `_report/usage/macro-hygiene-status.json`.
- Add `"optional": true` to any check in `macro-hygiene.objectives.json` when the evidence is informative but not required. Optional misses are recorded yet keep the objective in a ready state unless you run `--strict`.
- `python -m tools.autonomy.macro_hygiene --strict` treats optional checks as mandatory so you can audit drift without loosening normal operations.
- `python -m tools.agent.autonomy_status --json` now inlines the macro hygiene summary so readiness dashboards see gaps immediately.
- When the ledger changes, update this doc and the JSON file together so CI and operators stay aligned.
