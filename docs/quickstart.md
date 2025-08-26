# Quickstart

## 1) Clone
```bash
git clone https://github.com/octobrium/TEOF.git
cd TEOF

cat > quickstart.md <<'EOF'
# Quickstart

## 1) Clone
```bash
git clone https://github.com/octobrium/TEOF.git
cd TEOF

cat > STATUS.md <<'EOF'
<!-- repo-health:status -->
_Repo health checks (bootstrap+doctor) enforce workflow deterministically before every commit._

# TEOF Status (2025-08-25T00:20:46+00:00Z)

## Snapshot
- Capsule: /Users/evan/Documents/GitHub/TEOF/capsule/current -> v1.5
- Package: teof 0.1.0a2
- CLI: `teof brief` → writes `artifacts/ocers_out/<UTCSTAMP>/` and updates `artifacts/ocers_out/latest/`
- Artifacts latest: /Users/evan/Documents/GitHub/TEOF/artifacts/ocers_out/latest (ready: yes)

## Auto Objectives (detected)
- [todo] OBJ-A5 — Append STATUS refresh to pre-commit — Add `teof status --quiet || true` and `git add docs/STATUS.md || true` to .githooks/pre-commit

## Manual Objectives (optional)
- (none listed)

## Notes
- Keep `capsule/current` as a symlink.
- Python ≥3.9 for local dev.
