# Plan Justification — 2025-09-18-manager-heartbeat

## Why now
Agents currently infer who is acting as manager by scanning assignments or message streams. This fails if no manager is active or if multiple agents think someone else is covering. We need an explicit signal and guard.

## Proposal
Enhance coordination tooling to:
1. Surface active manager identities in `python -m tools.agent.bus_status` (and optionally a lightweight helper).
2. Emit a warning when no manager-role agent has logged a handshake/status within a configurable window.
3. Document the workflow so teams know how the heartbeat works and what to do when it fires.

## Receipts
- `_report/agent/codex-3/manager-heartbeat/notes.md`
- `_report/agent/codex-3/manager-heartbeat/tests.json`

## Tests / verification
- `pytest tests/test_agent_bus_status.py`
- New targeted test verifying manager detection (e.g., `tests/test_manager_status.py`).

## Safety
Read-only inspection of bus + manifest data; no destructive actions. Guard should degrade gracefully (log warning, non-blocking exit code by default).
