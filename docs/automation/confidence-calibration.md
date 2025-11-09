# Confidence Calibration Analytics

Reference for ND-068 (confidence calibration) documenting the pipeline,
receipts, and guardrails that replaced the earlier `_report/usage/` scratch
files.

## Pipeline summary

| Stage | CLI | Output |
| --- | --- | --- |
| Collect | `python3 -m tools.agent.confidence_calibration collect --out artifacts/confidence/<ts>.json` | Raw confidence samples with plan/task links |
| Normalize | `python3 -m tools.agent.confidence_calibration normalize artifacts/confidence/<ts>.json` | Normalized summary appended to `docs/reports/confidence-calibration.md` |
| Alerting | `python3 -m tools.agent.confidence_calibration alert --summary docs/reports/confidence-calibration.md` | Emits bus alerts when thresholds violated |

## Required receipts

1. `docs/reports/confidence-calibration.md` – rolling summary kept under
   version control.
2. `tools/agent/confidence_calibration.py` – CLI entrypoint.
3. `tests/test_confidence_calibration.py` – regression tests ensuring the CLI
   handles sample inputs.

These tracked artifacts replace the transient `_report/usage/confidence-calibration/*`
files originally referenced in the plan, making CI validation deterministic.
