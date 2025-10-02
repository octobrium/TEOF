# Autonomy Footprint Policy

The autonomy footprint tracks the size and cadence of automation code and receipts. Use the helper `python3 scripts/prune_autonomy_receipts.py` to prune aged receipts (default: keep latest 5 per directory, drop anything >30 days). Receipts pruned during CI/dry runs should be reviewed and committed when the footprint baseline is updated.

- After pruning, regenerate footprint entries via `python3 -m teof.bootloader status --quiet` to refresh the log.
- Update `docs/automation/autonomy-footprint-baseline.json` only when the program deliberately grows.
- Autonomy receipts exceeding 200 trigger warnings in status and preflight; prune or rotate before shipping.
