# Autonomy Stress Harness

**Purpose**: red-team `tools.autonomy.auto_loop` and conductor flows with deterministic scenarios before unattended runs.

## CLI

```bash
python -m tools.autonomy.stress_harness --scenarios docs/automation/autonomy-stress.sample.json --require-pass
```

Options:
- `--scenarios <path>`: JSON list or `{"scenarios": [...]}` wrapper describing cases.
- `--output <path>`: override receipt destination (defaults to `_report/usage/autonomy-stress/autonomy-stress-<timestamp>.json`).
- `--require-pass`: exit non-zero when a scenario expected to pass fails (CI guard hook).

## Scenario Schema

```json
{
  "name": "missing receipt guard test",
  "type": "missing_receipt",
  "severity": "high",
  "config": {
    "missing_receipt": true,
    "expected_result": "fail",
    "notes": "Should fail until receipts guard patched"
  }
}
```

Supported types (extensible via `SCENARIO_HANDLERS`):
- `missing_receipt`: fails when `missing_receipt` is true.
- `auth_dropout`: fails when `drops >= threshold`.
- `stuck_task`: fails when `heartbeat_gap_minutes > max_gap_minutes`.

`config.expected_result` defaults to `"pass"` and determines whether a failure is expected (e.g., intentional regression tests).

## Receipts
- Harness writes `_report/usage/autonomy-stress/*.json`, each with per-scenario results, counts, and a SHA-256 digest (see `_report/usage/autonomy-stress/sample-run.json` for a reference output).
- Attach the receipt path to your plan/tests (`python -m teof bus_message --receipt <path> ...`).
- CI can run `python -m tools.autonomy.stress_harness --scenarios docs/automation/autonomy-stress.sample.json --require-pass` (or your bespoke scenario file) to block promotion when critical safeguards regress.

## Integration Hooks
- Extend scenarios as new guardrails land (e.g., session heartbeat, conductor reconciliation).
- Future work: plug harness into `auto_loop` fixtures and push failures into `_report/usage/autonomy-stress/alerts.jsonl` for manager dashboards.
