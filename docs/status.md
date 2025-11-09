# TEOF Status (2025-11-09T16:07:57+00:00Z)

## Snapshot
- Capsule: /Users/evan/Documents/GitHub/TEOF/capsule/current -> v1.6
- Package: teof 0.1.0a2
- CLI: `teof brief` → writes `artifacts/systemic_out/<UTCSTAMP>/` and updates `artifacts/systemic_out/latest/`; `teof impact_bridge` links `memory/impact/log.jsonl` to `_plans/**/*.plan.json` and stores dashboards under `_report/impact/bridge/`; `teof scan --summary` keeps systemic guard counts streaming into `_report/usage/systemic-scan/ratchet-history.jsonl` by default (pass `--no-history` to opt out)
- Artifacts latest: /Users/evan/Documents/GitHub/TEOF/artifacts/systemic_out/latest (ready: yes)
- Authenticity dashboard: `_report/usage/external-authenticity.md` (auto-refreshes with each summary run)
- Exploratory lane: (inactive — use `teof-plan new <slug> --exploratory` to bootstrap)

## Autonomy Footprint
- Modules: 43 (Δ0) files · 7510 (Δ0) LOC · 248 (Δ0) helper defs
- Receipts: 1 (Δ0) JSON receipts under `_report/usage` containing 'autonomy'
- Recent Footprint Deltas:
  - 2025-11-09T16:07:57+00:00Z: modules=43, loc=7510, helpers=248, receipts=1
  - 2025-11-09T16:07:30+00:00Z: modules=43, loc=7510, helpers=248, receipts=1
  - 2025-11-09T16:07:17+00:00Z: modules=43, loc=7510, helpers=248, receipts=1

## CLI Capability Health
- Commands: 27 | missing tests: 0 | stale>30d: 0

## Automation Health
- Modules: 41 | missing receipts: 0 | stale>30d: 0 | missing tests: 0

## Auto Objectives (detected)
- [done] OBJ-A4 — Update docs/quickstart.md with editable install and CLI — Confirmed Quickstart snippet includes editable install + brief run
- [done] OBJ-A5 — Append STATUS refresh to pre-commit — Pre-commit hook refreshes docs/status.md

## Manual Objectives (optional)
- (none listed)

## Notes
- Keep `capsule/current` as a symlink.
- Python ≥3.9 for local dev.

