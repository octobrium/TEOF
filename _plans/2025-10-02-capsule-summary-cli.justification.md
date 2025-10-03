# Justification: 2025-10-02-capsule-summary-cli

- `docs/maintenance/capsule-cadence.md` still references a placeholder `python -m tools.capsule.cadence summary` command.
- CI guard `scripts/ci/check_capsule_cadence.py` only verifies receipts exist; generating `summary-latest.json` remains manual.
- Automating the summary keeps capsule cadence receipts deterministic and removes a manual blocker for QUEUE-039.
