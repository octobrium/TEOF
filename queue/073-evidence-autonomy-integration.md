# Task: Evidence + Autonomy Cycle Integration
Goal: unify the BTC scoreboard audit trail with autonomy hygiene automation so evidence stays observable without manual rebuilds.
Status: proposed (2025-11-03T21:30Z)
Notes: Consolidates remaining work from plans `2025-10-06-teof-btc-scoreboard`, `2025-10-19-autonomy-evolution`, and `2025-10-20-evidence-hygiene`; carries receipts forward under `2025-11-03-plan-hygiene-consolidation`.
Coordinate: S6:L5
Systemic Targets: S1 Unity, S4 Resilience, S6 Truth, S7 Power
Layer Targets: L5 Workflow, L6 Automation
Systemic Scale: 6
Principle Links: P1 (Observation bounds reasoning), P3 (Truth requires recursive test), P4 (Coherence before complexity), P6 (Proportional enforcement).
Sunset: when the BTC scoreboard emits automated audit receipts (`_report/impact/btc-ledger/audit-latest.json`) and the autonomy audit loop writes cadence + variance summaries each week under `_report/usage/autonomy-prune/`, with plan hygiene validators consuming both outputs.
Fallback: escalate to governance if audit automation cannot land; document temporary manual procedures with receipts and update systemic bindings.

Readiness Checklist:
- docs/impact/btc-ledger.md
- tools/autonomy/backlog_synth.py
- _report/usage/autonomy-prune/20251103-integrated-backlog.json
- _plans/2025-11-03-plan-hygiene-consolidation.plan.json

Receipts to Extend:
- _report/impact/btc-ledger/audit-latest.json (new automated audit summary)
- _report/usage/autonomy-prune/cadence-latest.json (autonomy audit loop output)
- memory/log.jsonl (append observation once automation is active)
