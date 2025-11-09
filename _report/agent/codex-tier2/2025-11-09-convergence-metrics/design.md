# Convergence Metrics Design — 2025-11-09

- Enumerated collector → aggregator → guard pipeline for ND-071.
- Locked telemetry schema (per-node drift, aggregate coherence band) with CLI commands `collect`, `aggregate`, `report`, `guard`.
- Defined receipts: `_report/usage/convergence-metrics/plan-latest.json` (plan inventory) + `_report/usage/convergence-metrics/telemetry-latest.json` (guard feed).
- Documented CLI wiring + CI expectations inside `docs/automation/convergence-metrics.md` to satisfy plan S2.
