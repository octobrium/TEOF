# TEOF Status (2025-08-24T21:58:26+00:00Z)

## Snapshot
- Capsule: /Users/evan/Documents/GitHub/TEOF/capsule/current -> v1.5
- Package: teof 0.1.0a2
- CLI: `teof brief` → writes `artifacts/ocers_out/<UTCSTAMP>/` and updates `artifacts/ocers_out/latest/`
- Artifacts latest: /Users/evan/Documents/GitHub/TEOF/artifacts/ocers_out/latest (ready: no)

## Auto Objectives (detected)
- [todo] OBJ-A1 — Generate brief artifacts — Run `teof brief` once to create artifacts/ocers_out/latest/{brief.json,score.txt}
- [todo] OBJ-A5 — Append STATUS refresh to pre-commit — Add `teof status --quiet || true` and `git add docs/STATUS.md || true` to .githooks/pre-commit

## Manual Objectives (optional)
- (none listed)

## Notes
- Keep `capsule/current` as a symlink.
- Python ≥3.9 for local dev.
