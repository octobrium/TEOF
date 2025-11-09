# TEOF Status (2025-11-09T05:16:45+00:00Z)

## Snapshot
- Capsule: /Users/evan/Documents/GitHub/TEOF/capsule/current -> v1.6
- Package: teof 0.1.0a2
- CLI: `teof brief` → writes `artifacts/systemic_out/<UTCSTAMP>/` and updates `artifacts/systemic_out/latest/`
- Artifacts latest: /Users/evan/Documents/GitHub/TEOF/artifacts/systemic_out/latest (ready: yes)
- Authenticity dashboard: `_report/usage/external-authenticity.md` (auto-refreshes with each summary run)
- Exploratory lane: (inactive — use `teof-plan new <slug> --exploratory` to bootstrap)

## Autonomy Footprint
- Modules: 36 (+1) files · 6258 (+167) LOC · 194 (+5) helper defs
- Receipts: 1 (Δ0) JSON receipts under `_report/usage` containing 'autonomy'
- Recent Footprint Deltas:
  - 2025-11-09T05:16:45+00:00Z: modules=36, loc=6258, helpers=194, receipts=1
  - 2025-11-09T05:06:36+00:00Z: modules=35, loc=6091, helpers=189, receipts=1
  - 2025-11-09T05:01:58+00:00Z: modules=35, loc=6091, helpers=189, receipts=1

## CLI Capability Health
- Commands: 20 | missing tests: 0 | stale>30d: 0

## Automation Health
- Modules: 34 | missing receipts: 0 | stale>30d: 0 | missing tests: 0

## Auto Objectives (detected)
- [done] OBJ-A4 — Update docs/quickstart.md with editable install and CLI — Confirmed Quickstart snippet includes editable install + brief run
- [done] OBJ-A5 — Append STATUS refresh to pre-commit — Pre-commit hook refreshes docs/status.md

## Manual Objectives (optional)
- (none listed)

## Notes
- Keep `capsule/current` as a symlink.
- Python ≥3.9 for local dev.
