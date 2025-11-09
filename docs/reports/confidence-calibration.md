# Confidence Calibration Summary (2025-11-09)

| Metric | Value |
| --- | --- |
| Samples ingested | 142 |
| Plans covered | 18 |
| Tasks covered | 27 |
| Alerts raised | 2 (AUTH-PRIMARY_TRUTH, AUTH-UNASSIGNED) |

## Highlights

- Confidence gaps traced to outdated authenticity receipts (see
  `docs/automation/authenticity-stability.md`).
- Normalized summaries appended via `python3 -m tools.agent.confidence_calibration normalize`.
- Telemetry feeds into the convergence metrics pipeline (`docs/automation/convergence-metrics.md`).

This file replaces the transient `_report/usage/confidence-calibration/*.json`
artifacts so strict plan validation can rely on a tracked receipt.
