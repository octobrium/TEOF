# Agent Proposal Justification — 2025-09-18-prune-script

## Why this helps
Pruning is documented but manual; a helper script will keep `_plans/` lean without ad-hoc shell. Codex-3 can implement it quickly while the workflow is fresh.

## Proposed change
Implement `tools/maintenance/prune_artifacts.py` to move stale plan + receipt artifacts into `_apoptosis/<timestamp>/`, add a targeted pytest, and refresh docs/maintenance/pruning-cadence.md with usage instructions.

## Receipts to collect
- `_report/agent/codex-3/prune-script/pytest.json`
- `_report/agent/codex-3/prune-script/notes.md`

## Tests / verification
- `pytest tests/test_prune_artifacts.py`

## Ethics & safety notes
File operations remain inside repo; ensure dry-run mode exists to preview changes.
