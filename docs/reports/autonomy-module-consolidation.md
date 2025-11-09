# Autonomy Module Consolidation Summary (2025-11-09)

- `tools.autonomy.module_consolidate` CLI provides `inventory`, `plan`,
  and `telemetry` subcommands. Receipts live in `_report/usage/autonomy-module-consolidation/`
  but this tracked summary captures the published plan.
- Shared primitives extracted into `tools.autonomy.shared_bus`.
- Tests: `tests/test_module_consolidate.py`, `tests/test_shared_bus.py`.

## Current plan

```json
{
  "schema": "autonomy.module_consolidation.plan/v1",
  "services": ["coordination", "execution", "signal"],
  "modules": 27,
  "shared_primitives": ["bus.publish", "bus.subscribe", "receipt.normalize"]
}
```

Use `python3 -m tools.autonomy.module_consolidate plan --format json` to regenerate
and commit updates when the service map changes.
