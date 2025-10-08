# Pruning Cadence

The pruning helper keeps `_plans/` and `_report/**` light so new sessions do not sift through stale artifacts.

## Daily Sweep
1. Preview the sweep:
   ```bash
   python -m tools.maintenance.prune_artifacts --dry-run
   ```
2. If the output looks correct, re-run without `--dry-run` to archive the listed entries.

Each run groups moves under `_apoptosis/<stamp>/…` for quick reversal and audit.

## Defaults
- **Cutoff:** artifacts older than 72 hours move to `_apoptosis/`. Override via `--cutoff-hours 24` (or any float).
- **Targets:** `_plans`, `_report/agent`, `_report/manager`, `_report/planner`, `_report/runner`, `_report/usage`. Limit the sweep with repeated `--target <path>`.
- **Stamp:** the destination stamp defaults to the current UTC time. Pass `--stamp 20250101T000000Z` when you need deterministic receipts.

The helper relocates entire plan files and per-task receipt directories. Active plans (recently touched or still in progress) stay put.

## Testing / CI Hooks
- Unit coverage: `pytest tests/test_prune_artifacts.py` (also safe for smoke tests).
- Integrations can invoke the module with `--root <tmpdir>`; the helper does not touch files outside the provided root.

## Safety Notes
- Moves are reversible: copy or move items back from `_apoptosis/<stamp>/`.
- The script does not delete; empty directories left behind remain for future runs.
- Review dry-run output before applying in multi-agent sessions.
