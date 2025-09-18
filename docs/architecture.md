<!-- markdownlint-disable MD013 -->
Status: Normative
Purpose: Contracts, layout, mechanisms (offline, lineage)
Change process: PR + 2 maintainers (one must be core)
Compatibility: SemVer; deprecations get one minor window

# TEOF Repo Architecture (v1.5, minimal)

## Allowed top-level


- `capsule/`        — immutable capsule + hashes (see `capsule/README.md` for active version and per-release `STATUS.md` markers)

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

## Promotion policy

Authoritative criteria and process live in [`docs/promotion-policy.md`](promotion-policy.md). Keep this file minimal and defer to that policy to avoid drift.

## New top-level folders

Avoid by default. If truly needed, add a 1-page TEP in `rfcs/` (purpose, contract, alternatives, rollback) and update this file.

## L4 bindings (canon ↔ automation)

- Binding matrix: [`governance/core/L4 - architecture/bindings.yml`](../governance/core/L4%20-%20architecture/bindings.yml) records which objectives/properties are enforced by specific tests, scripts, and receipts.
- Update the matrix whenever a new guard lands or coverage shifts; gaps stay explicit until automation exists.

