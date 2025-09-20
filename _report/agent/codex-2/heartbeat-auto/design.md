# Heartbeat auto-hook design (2025-09-19T214948Z-heartbeat-auto-codex2)

## Goal
Automate emitting a `bus_event status` heartbeat when an agent wraps a working session so manager dashboards stay green without manual pings.

## Proposed approach
- Extend `tools.agent.manifest_helper session-save` (our canonical session wrap command) to log a status heartbeat after it snapshots the manifest/branch.
- Produce the heartbeat via a small helper (`tools.agent.heartbeat.emit_status`) that:
  - Resolves the agent id from manifest (or argument override).
  - Builds a status summary like `Session wrap: <label>` and attaches branch/label metadata.
  - Supports `--dry-run` so tests (and rehearsals) can assert behaviour without writing to `_bus/events`.
  - Surfaces `--heartbeat-summary`/`--heartbeat-meta key=value` overrides to document shift/role context.
- Default behaviour: heartbeat logging is on; operators can disable with `--no-heartbeat` (e.g., during experiments).
- Tests will monkeypatch `manifest_helper` paths to a tmp repo and assert that `session-save --dry-run` prints the payload, then that a real run writes a status event under `_bus/events/events.jsonl`.
- Docs (`docs/parallel-codex.md`) will note that `session-save` now records the heartbeat automatically so cadences stay fresh.

## Receipts
- Implementation: `tools/agent/manifest_helper.py`, new helper module (`tools/agent/heartbeat.py`).
- Tests: `tests/test_manifest_helper.py` (+ optional `tests/test_agent_heartbeat.py`).
- Docs: update heartbeat workflow snippet.
