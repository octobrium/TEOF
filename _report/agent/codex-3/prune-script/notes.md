# Queue-015 Prune Helper Notes
- Implemented `tools/maintenance/prune_artifacts.py` with defaults for `--cutoff-hours 72`, `--dry-run`, optional `--target`, and timestamp overrides.
- Added regression coverage in `tests/test_prune_artifacts.py` for discovery (dry-run) and actual move behaviour.
- Published usage guidance in `docs/maintenance/pruning-cadence.md` and linked from `docs/agents.md` so crews can schedule the daily sweep.
