# TEOF Architecture & Repo Map (v1.5)

## Purpose
Minimal, auditable kernel + deterministic tools. Applications live outside.

## Top-level
- `capsule/` — immutable capsule and hashes
- `extensions/` — canonical code (packaged); import surface `extensions.…`
  - `validator/` — OCERS validators & scorers
  - `ogs/`       — evaluator logic (if split out)
- `experimental/` — active candidates; not packaged
- `archive/` — frozen history
- `cli/` — thin entrypoints (optional)
- `docs/` — Quickstart, Promotion Policy, this map, examples/goldens
- `governance/` — anchors.json (append-only events), release docs
- `rfcs/` — TEPs/RFCs
- `scripts/` — freeze.sh, policy checks, release helpers
- `.github/` — CI
- Root files — packaging & policy: `pyproject.toml`, `Makefile`, `README.md`, `CHANGELOG.md`, `LICENSE`

## Boundaries
- Only `extensions/` is packaged / exported as console scripts.
- `extensions/` must NOT import from `experimental/` or `archive/`.
- Rule changes require: updated goldens, anchors event, changelog line.

## When to add a new top-level folder?
Only if it’s one of the categories above. Applications (e.g., TEOF Score™) should be separate repos.
