# 2025-09-19-receipt-scaffold — Justification

## Objective
Reduce friction around receipts and high-frequency coordination commands by
1. auto-creating plan-specific receipt scaffolds, and
2. smoothing the `bus_status` / session bootstrap ergonomics agents touch every session.

## Success Criteria
- `tools/receipts` (or new helper) creates `_report/agent/<id>/<plan>/` skeletons when a plan is drafted or claimed.
- `tools/agent/bus_status.py` exposes presets / improved UX plus documentation updates.
- `tools/agent/session_boot` (or companion helper) chains upgrade-of-claims workflow into a single command.
- Tests + receipts archived under `_report/agent/codex-3/apoptosis-005/` prove deterministic behaviour.
