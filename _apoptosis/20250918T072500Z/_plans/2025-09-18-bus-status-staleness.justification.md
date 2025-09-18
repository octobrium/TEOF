# Justification — 2025-09-18-bus-status-staleness

## Why now
- Default `bus_status` output can be noisy during multi-agent sessions; adding a relative window keeps summaries focused without manual timestamps.
- Aligns with backlog item `queue/008-bus-status-staleness` and complements recently added filters.

## Scope
- Introduce `--window-hours` option (24h default, `0` disables) alongside existing `--since` support.
- Update JSON output metadata, documentation references, and regression tests covering window enable/disable cases.

## Receipts
- `_report/agent/codex-3/bus-status-staleness/pytest.json`

## Links
- Queue task: `queue/008-bus-status-staleness.md`
- Claim record: `_bus/claims/QUEUE-008.json`
