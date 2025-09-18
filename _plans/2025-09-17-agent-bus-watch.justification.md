# Agent Proposal Justification

## Why this helps
Parallel Codex runs rely on `_bus/events/events.jsonl`, but today agents must open the file manually. Adding a simple watcher/`--since` tool improves coordination visibility so peers don't miss status updates.

## Proposed change
Add a `tools/agent/bus_watch.py` CLI that tails bus events or filters by timestamp/agent. Update documentation to advertise the workflow and add minimal tests.

## Receipts to collect
- `_report/agent/codex-2/agent-bus-watch/pytest.json`

## Tests / verification
- `pytest tests/test_agent_bus.py` (TODO)

## Ethics & safety notes
None.
