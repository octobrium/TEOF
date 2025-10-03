# Dirty Handoff Auto-Resolver — Design

## Goals
- Scan `_report/session/<agent>/dirty-handoff/dirty-*.txt` receipts and build a summary (owner, latest captured_at, age, receipt path).
- Flag receipts older than configurable thresholds, optionally writing escalation JSON and sending bus status messages.
- Provide exit codes so automation can treat stale handoffs as CI warnings or failures.
- Integrate cleanly with existing guards (no modifications to receipts, append-only).

## Proposed CLI
`python -m tools.agent.dirty_autoresolver [options]`

Options:
- `--max-age-minutes <int>`: considered stale if newer receipt age >= threshold (default 60).
- `--warn-age-minutes <int>`: middle tier for “nudge soon” hints (default 30).
- `--output <path>`: write JSON summary (agents, receipts, counts).
- `--bus-message`: when set, send a status message to manager-report summarising stale receipts.
- `--dry-run`: compute summary without writing or messaging.
- `--now <iso>`: injectable current time for testing.

Summary schema (JSON):
```
{
  "generated_at": "ISO",
  "warn_threshold_minutes": 30,
  "fail_threshold_minutes": 60,
  "agents": [
    {
      "agent_id": "codex-3",
      "latest_receipt": "_report/session/codex-3/...",
      "captured_at": "ISO",
      "age_minutes": 42.5,
      "status": "warn"  # ok | warn | fail
    }, ...
  ]
}
```

## Behaviour
1. Recursively glob dirty receipts, parse header lines (`# agent=`, `# captured_at=`). When missing, fallback to file mtime.
2. For each agent choose the most recent receipt; compute age.
3. Determine status: `fail` if age >= max-age, `warn` if >= warn-age, else `ok`.
4. Output JSON summary and human-readable table to stdout.
5. Non-zero exit: return 2 when any `fail`, 1 when only `warn`, 0 otherwise.
6. If `--bus-message`, compose `tools.agent.bus_message` status entry with summary + attached JSON receipt (if output path provided).

## Integration Hooks
- Coord dashboard already consumes dirty receipts; summary can be stored under `_report/agent/<runner>/dirty-autoresolver/summary-<timestamp>.json`.
- Later automation (cron/CI) can run with `--bus-message` so managers see escalations in `manager-report`.

## Tests
- Use tmp_path to mock `_report/session/<agent>/dirty-handoff/` with sample receipts.
- Validate parsing, status classification, output JSON, exit codes, messaging (monkeypatch bus_message).

## Future Enhancements
- Auto-open `queue/` tasks when fail threshold exceeded.
- Auto-triad with `session_boot` to resolve branch/manifest mismatches.
