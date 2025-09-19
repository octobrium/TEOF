# 2025-09-21-coordination-dashboard — Justification

## Objective
Create a lightweight coordination dashboard/report aggregating bus events, plan status, heartbeat alerts, and manager directives for quick situational awareness.

## Success Criteria
- Dashboard CLI (or scheduled report) implemented, emitting deterministic JSON/markdown under `_report/manager/`.
- Integrated with heartbeat alerts + receipt scaffolding to highlight idle tasks automatically.
- Docs/manager workflow updated to reference the new surface.
