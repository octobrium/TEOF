# Agent Bus Awareness Improvements

## Why this helps
Parallel agents now rely on `_bus/events/events.jsonl` manually. Providing first-class commands/docs for tailing and summarizing reduces coordination latency and prevents missed updates.

## Proposed change
1. Evaluate current tools (`bus_status`, `session_boot`) and identify gaps (e.g., streaming/tailing).
2. Add a helper (e.g., `bus_watch`) or documentation snippet for continuous monitoring.
3. Sync with Codex-2 to confirm the workflow and capture feedback in the plan notes.

## Receipts to collect
- CLI command outputs (`python -m tools.agent.bus_status --limit 20` snapshots)
- Updated doc references (`docs/parallel-codex.md`, `.github/AGENT_ONBOARDING.md`)

## Tests / verification
- Run the new helper or documented command to ensure it reflects live bus events.

## Ethics & safety notes
No secret exposure; only surfaces existing bus data.
