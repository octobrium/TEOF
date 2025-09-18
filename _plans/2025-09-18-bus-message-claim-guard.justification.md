# Agent Proposal Justification — 2025-09-18-bus-message-claim-guard

## Why this helps
`bus_message` is the parallel coordination surface to `bus_event`. After the event guard landed, status broadcasts can still bypass claims via `bus_message`, leaving the ledger inconsistent and reintroducing overlapping engineers. Aligning both CLIs keeps every task update behind a claim check.

## Proposed change
Add the same claim ownership enforcement used in `bus_event` to `tools.agent.bus_message`, update the CLI error path, and extend regression coverage. Mirror the guardrail documentation where the CLI is referenced.

## Receipts to collect
- `_report/agent/codex-2/bus-message-claim-guard/pytest.json`

## Tests / verification
- `pytest tests/test_agent_bus_message.py`

## Ethics & safety notes
Local tooling only; no external dependencies.
