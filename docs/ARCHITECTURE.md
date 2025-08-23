# TEOF Repo Architecture (v1.5, minimal)

## Allowed top-level
capsule/        – immutable capsule + hashes
extensions/     – canonical, packaged code (import surface: extensions.…)
experimental/   – active candidates (NOT packaged)
archive/        – frozen history (NOT packaged)
cli/            – thin entrypoints (optional)
docs/           – Quickstart, Architecture, Promotion Policy, examples/goldens
governance/     – anchors.json (append-only), release notes
rfcs/           – TEPs/RFCs
scripts/        – repo scripts (policy guard, freeze, release helpers)
.github/        – CI
README.md CHANGELOG.md LICENSE Makefile pyproject.toml .gitignore

## Placement rules
- Kernel code → extensions/
- Prototypes/candidates → experimental/ (promote only via Promotion Policy)
- Retired/snapshots → archive/
- Human-facing prose, examples, diagrams → docs/
- Release/provenance → governance/
- One-off helpers → scripts/
- Apps (TEOF Score™, web demos) → separate repos

## Naming
- modules: snake_case; packages: singular; CLI entrypoints live in extensions/… with main()
- no imports from experimental/ or archive/ inside extensions/

## Promotion policy (summary)
- Deterministic, spec-aligned, CI-covered, minimal deps, anchored; docs updated.
