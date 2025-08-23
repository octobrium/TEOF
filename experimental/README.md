# legacy/

**Purpose:** safe parking for non-runtime code and artifacts (experiments, old packages, ops scripts, fixtures).
- Not read by CI/Makefile/CLI.
- Use this instead of deleting when unsure.
- Promotion back to trunk requires a PR with Objective line (Class/Why/MinimalStep/Direction).

## Layout
- `experiments/` — one-off research, retired prototypes (e.g., branches_thin, ogs).
- `ops/` — operational scripts & helpers (e.g., reporting layout); subfolders: `scripts/`, `tools/`.
- `packages/` — old or archived libraries (e.g., `ocers/`).
- `bootloaders/` — bootstrap code (e.g., LLM bootstraps).
- `tests/` — archived fixtures (not used by trunk).

## Hygiene
- No imports from `legacy/` in trunk code.
- Consider pruning `experiments/*` untouched for 90 days.
