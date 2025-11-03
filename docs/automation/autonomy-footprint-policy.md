# Autonomy Footprint Policy

The autonomy footprint tracks the size and cadence of automation code and receipts. Use the helper `python3 scripts/prune_autonomy_receipts.py` to prune aged receipts (default: keep latest 5 per directory, drop anything >30 days). Receipts pruned during CI/dry runs should be reviewed and committed when the footprint baseline is updated.

- After pruning, regenerate footprint entries via `python3 -m teof.bootloader status --quiet` to refresh the log.
- Update `docs/automation/autonomy-footprint-baseline.json` only when the program deliberately grows.
- Autonomy receipts exceeding 200 trigger warnings in status and preflight; prune or rotate before shipping.

## Cadence guard (new in 2025-11)

- Run `python -m tools.autonomy.prune_cadence` each hygiene sweep.  
  - Exit code `0` → cadence healthy (receipt captured unless `--no-receipt`).  
  - Exit code `1` → pruning is due; the summary lists all triggering reasons.
- Cadence rules:
  1. **Interval** — prune at least every 14 days (`--interval-days` adjustable per program).  
  2. **Receipt volume** — prune immediately when autonomy receipts ≥ 160.  
  3. **Module growth** — prune or split work when automation modules grow by > 6 files over the baseline.
- Receipts land in `_report/usage/autonomy-prune/` and include: generated timestamp, current footprint, baseline, reasons, next deadline, and the last prune receipt path. This keeps Observation (L0) and Workflow (L5) aligned.
- When cadence reports “due”, open a plan under `_plans/hygiene/` referencing the cadence receipt and include the pruning command trail so automation can replay the recovery.
