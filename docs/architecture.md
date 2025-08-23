# TEOF Repo Architecture (v1.5, minimal)

## Allowed top-level
- `capsule/`        — immutable capsule + hashes
- `extensions/`     — canonical, packaged code (import surface: `extensions.…`)
- `experimental/`   — active candidates (NOT packaged)
- `archive/`        — frozen history (NOT packaged)
- `docs/`           — Quickstart, Architecture, Promotion Policy, examples/goldens
- `governance/`     — `anchors.json` (append-only), release notes
- `rfcs/`           — TEPs/RFCs
- `scripts/`        — repo scripts (policy guard, freeze, release helpers)
- `.github/`        — CI
- Root files: `README.md` `CHANGELOG.md` `LICENSE` `Makefile` `pyproject.toml` `.gitignore`
- *(Optional)* `cli/` — thin entrypoints only; prefer console scripts from `extensions/…:main()`

## Placement rules
- Kernel code → `extensions/`
- Prototypes/candidates → `experimental/` (promote only via Promotion Policy)
- Retired/snapshots → `archive/`
- Human-facing prose, examples, diagrams → `docs/`
- Release/provenance → `governance/`
- One-off helpers → `scripts/`
- Apps (TEOF Score™, web demos) → separate repos

## Naming
- Modules: `snake_case`; packages: singular; CLI entrypoints expose `main()` in `extensions/…`
- **No imports** from `experimental/` or `archive/` inside `extensions/`

## Promotion policy (summary)
Promote from `experimental/` → `extensions/` only if ALL:
1. **Deterministic** (same inputs → same outputs; triple-run OK)  
2. **Spec-aligned** (OCERS/OGS shapes current; goldens updated if rules changed)  
3. **CI-covered** (examples under `docs/examples/**`; regressions fail CI)  
4. **Minimal deps** and clear `main()` / import path  
5. **Anchored** change (append event in `governance/anchors.json` with `prev_content_hash`)  
6. **Docs updated** (Quickstart and/or module README show exact commands)

## New top-level folders
Avoid by default. If truly needed, add a 1-page TEP in `rfcs/` (purpose, contract, alternatives, rollback) and update this file.
