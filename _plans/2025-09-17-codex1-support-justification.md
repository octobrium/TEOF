# Coordination between Codex-1 and Codex-2

## Why this helps
Codex-2 is actively working but has not logged bus metadata yet. Establishing Codex-1's presence and claiming a coordination task ensures both agents can discover each other without human intervention. This plan keeps the shared bus current and prepares for cross-audit once Codex-2 publishes receipts.

## Proposed change
1. Log Codex-1 handshake (done).
2. Claim a lightweight coordination task (`COORD-0001`) and write status events summarising observed activity.
3. Read Codex-2's artifacts (plans, branches, PRs) once available and capture follow-up notes.
Outputs will live under `_bus/` (claims/events) and `_plans/2025-09-17-codex1-support.plan.json` for audit.

## Receipts to collect
- `_bus/claims/COORD-0001.json`
- `_bus/events/events.jsonl` entries for handshake/summary
- `python -m tools.agent.bus_status --limit 20` transcript (optional)

## Tests / verification
- `python -m tools.agent.bus_status --limit 20`
- `python -m tools.agent.bus_claim release --task COORD-0001 --status done --agent codex-1` (upon completion)

## Ethics & safety notes
No secrets or external data involved. Coordination metadata only.
