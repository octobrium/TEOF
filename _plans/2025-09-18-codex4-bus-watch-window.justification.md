# Agent Proposal Justification — 2025-09-18-codex4-bus-watch-window

## Why this helps
The repo reset removed the previous `bus_watch --window-hours` implementation while docs (`docs/agents.md`, `docs/collab-support.md`) still instruct agents to rely on the flag. Without the staleness window, operators must manually juggle timestamps or tolerate very old events, reducing situational awareness during multi-agent sessions. QUEUE-009 requests restoring this behaviour to mirror the bus_status window semantics.

## Proposed change
Introduce a `--window-hours` option to `tools.agent.bus_watch` that filters events older than `now - window`. Default to 24h, allow `0` to disable, and reject negatives. Update filtering helpers, streaming logic, and CLI help, plus extend `tests/test_agent_bus_watch.py` to cover windowed selection. Refresh docs mentioning the command so they explain the default/off behaviour.

## Receipts to collect
- `_report/agent/codex-4/bus-watch-window/pytest.json` (pytest run covering new behaviour)
- Any additional receipts if doc tooling requires (none expected).

## Tests / verification
- `pytest tests/test_agent_bus_watch.py`

## Ethics & safety notes
None — local CLI + docs only.
