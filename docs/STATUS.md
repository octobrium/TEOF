# TEOF Status (2025-09-21T19:52:00+00:00Z)

## Snapshot
- Capsule: /Users/evan/Documents/GitHub/TEOF/capsule/current -> v1.6
- Package: teof 0.1.0a2
- CLI: `teof brief` → writes `artifacts/ocers_out/<UTCSTAMP>/` and updates `artifacts/ocers_out/latest/`
- Artifacts latest: /Users/evan/Documents/GitHub/TEOF/artifacts/ocers_out/latest (ready: yes)
- Authenticity dashboard: `_report/usage/external-authenticity.md` (auto-refreshes with each summary run)

## Auto Objectives (detected)
- [todo] OBJ-A4 — Update docs/quickstart.md with editable install and CLI — Include `pip install -e .` and `teof brief` usage in Quickstart.
- [todo] OBJ-A5 — Append STATUS refresh to pre-commit — Add `teof status --quiet || true` and `git add docs/STATUS.md || true` to .githooks/pre-commit

## Manual Objectives (optional)
- (none listed)

## Notes
- Keep `capsule/current` as a symlink.
- Python ≥3.9 for local dev.
