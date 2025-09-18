# Agent Proposal Justification

## Why this helps
`bus_status` currently dumps every claim and recent event, which is noisy for simultaneous sessions. Filtering by agent or status and emitting JSON would let Codex peers and tooling focus on relevant updates without manual parsing.

## Proposed change
Extend `tools/agent/bus_status.py` with filtering flags (`--agent`, `--active-only`) and an optional `--json` mode. Update documentation to advertise the workflow and add unit tests covering the filters.

## Receipts to collect
- `_report/agent/codex-2/agent-bus-status/pytest.json`

## Tests / verification
- `pytest tests/test_agent_bus_status.py`

## Ethics & safety notes
None.
