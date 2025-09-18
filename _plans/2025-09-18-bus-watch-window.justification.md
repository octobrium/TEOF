# Justification — 2025-09-18-bus-watch-window

## Why now
- After adding a staleness window to `bus_status`, the streaming `bus_watch` CLI should mirror the same behaviour for consistency.
- Ensures idle/monitoring agents see recent coordination without manual filtering, aligning with `queue/009-bus-watch-window.md`.

## Scope
- Add `--window-hours` flag to `tools/agent.bus_watch` with validation and default 24h window.
- Extend unit tests and documentation to describe the shared semantics with `bus_status`.

## Receipts
- `_report/agent/codex-3/bus-watch-window/pytest.json`

## Links
- Queue task: `queue/009-bus-watch-window.md`
- Claim record: `_bus/claims/QUEUE-009.json`
