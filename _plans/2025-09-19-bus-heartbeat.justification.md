# 2025-09-19-bus-heartbeat — Justification

## Objective
Automate detection of stale coordination loops by monitoring bus heartbeats and emitting actionable alerts, reducing manual manager polling.

## Success Criteria
- Heartbeat watcher runs locally or via CI cron, configurable per agent/manager windows.
- Emits structured receipts under `_report/agent/codex-2/apoptosis-004/` and logs to `_bus/events` when alerts fire.
- Planner validation + targeted pytest cover the new automation (unit + smoke tests).

## Risks / Mitigations
- **False positives:** add configurable grace period + dry-run mode before full activation.
- **Noise:** aggregate alerts and respect existing manager notes to avoid spam.
