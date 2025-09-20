# Design log — heartbeat integration (2025-09-19)

Goal: confirm the heartbeat automation loop stays green after session bootstraps. We’ll extend `session_boot` with a `--with-dashboard` option that runs the coordination dashboard immediately after sync, storing a receipt. Tests will cover the CLI integration, and completing the plan will require capturing a real snapshot + heartbeat event receipts.

Scope:
- Add an optional `--with-dashboard` flag (default off) to `tools.agent.session_boot` to run `coord_dashboard` right after sync and handshake.
- Allow passing `--dashboard-output` to specify receipt location (default under `_report/agent/<id>/session_boot/`).
- Record design decisions + tests under `_report/agent/codex-4/2025-09-19-heartbeat-integration-codex4/`.
