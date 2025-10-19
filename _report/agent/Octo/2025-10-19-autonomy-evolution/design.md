# Design log for 2025-10-19-autonomy-evolution

## Mission
Create a self-sustaining coordination layer that keeps the backlog, execution, and auditing loops aligned with TEOF’s north-star principles without relying on manual orchestration.

## Properties (L3 targets)
- **Backlog truthfulness:** every backlog entry must cite observations and systemic obligations before it appears in `_plans/next-development.todo.json`.
- **Coordinated autonomy:** orchestration chooses work only when guard conditions (authenticity, CI, open claims) are satisfied and records receipts for every run.
- **Self-correcting audit:** completed work is re-verified on a cadence; divergences trigger circuit breakers and remediation plans.

## Scope overview
1. **Autonomous backlog steward** – ingest vision docs + receipts, propose backlog updates with observations and plan suggestions, retire stale items, and emit receipts so humans can ratify or revert.
2. **Manager orchestration service** – extend the coordinator service to schedule multiple seats, balance claims, and surface health metrics (scan, systemic, worker outcomes) centrally.
3. **Autonomous audit loop** – replay receipts, compare expected vs. actual outcomes, and file repair tasks automatically when drift is detected.

## Constraints
- Changes must remain deterministic and reversible (existing guard/orchestrator receipts).
- Every automation action logs to the bus with severity + status so operators can monitor from `manager-report`.
- Audit loops must run on a bounded cadence (default 24h) and refuse to proceed when authenticity or CI trust drops below guard thresholds.
