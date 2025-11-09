# ND-065 Build Artifact Guard Requirements (2025-11-09T05:43Z)

- Identify directories/artifacts to block (dist/, build/, coverage artifacts, node_modules clones).
- CLI `python -m tools.autonomy.build_guard check --paths ...` to scan worktree and emit receipts.
- CI hook integration + docs update for guard usage.
