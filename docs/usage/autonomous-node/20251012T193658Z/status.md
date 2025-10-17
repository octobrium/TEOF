# TEOF Status (2025-10-12T19:36:58+00:00Z)

## Snapshot
- Capsule: /Users/evan/Documents/GitHub/TEOF/capsule/current -> v1.6
- Package: teof 0.1.0a2
- CLI: `teof brief` → writes `artifacts/systemic_out/<UTCSTAMP>/` and updates `artifacts/systemic_out/latest/`
- Artifacts latest: /Users/evan/Documents/GitHub/TEOF/artifacts/systemic_out/latest (ready: yes)
- Authenticity dashboard: `_report/usage/external-authenticity.md` (auto-refreshes with each summary run)

## Autonomy Footprint
- Modules: 24 (+1) files · 4121 (+128) LOC · 125 (+11) helper defs
- Receipts: 1 (Δ0) JSON receipts under `_report/usage` containing 'autonomy'
- Recent Footprint Deltas:
  - 2025-10-12T19:36:58+00:00Z: modules=24, loc=4121, helpers=125, receipts=1
  - 2025-10-11T20:05:19+00:00Z: modules=23, loc=3993, helpers=114, receipts=1
  - 2025-10-11T19:53:45+00:00Z: modules=23, loc=3993, helpers=114, receipts=1

## CLI Capability Health
- Commands: 11 | missing tests: 0 | stale>30d: 0

## Automation Health
- Modules: 22 | missing receipts: 4 | stale>30d: 4 | missing tests: 2
- Stale receipts (limit 5):
  - tools.autonomy.audit_guidelines: last_receipt=never
  - tools.autonomy.ethics_gate: last_receipt=never
  - tools.receipts.log_event (impact preset): last_receipt=never
  - tools.autonomy.node_runner: retired after 2025-10-18
- No direct tests detected (limit 5):
  - tools.autonomy.audit_guidelines: last_receipt=never
  - tools.autonomy.node_runner: retired after 2025-10-18

## Auto Objectives (detected)
- [done] OBJ-A4 — Update docs/quickstart.md with editable install and CLI — Confirmed Quickstart snippet includes editable install + brief run
- [done] OBJ-A5 — Append STATUS refresh to pre-commit — Pre-commit hook refreshes docs/status.md

## Manual Objectives (optional)
- (none listed)

## Notes
- Keep `capsule/current` as a symlink.
- Python ≥3.9 for local dev.
