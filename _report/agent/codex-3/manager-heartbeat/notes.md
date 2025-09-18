# Manager Heartbeat Survey — 2025-09-18

Signals observed:
- **Manifests:** agents declare desired roles in `AGENT_MANIFEST*.json` (e.g., `desired_roles: ["manager"]`). Current manager manifest is `AGENT_MANIFEST.codex-manager.json`.
- **Assignments:** `_bus/assignments/<task>.json` captures a `manager` field for each queued task; most recent governance/consensus tasks list `codex-4`.
- **Events:** Managers typically emit `handshake` or `status` events tagged with plan IDs (e.g., `2025-09-18-governance-bridge`). No canonical heartbeat window exists.
- **Messages:** `_bus/messages/manager-report.jsonl` aggregates manager updates but is optional; absence here doesn’t guarantee no manager online.

Key gaps:
- No single CLI call answers “who is the active manager?”
- If every manager goes offline, no automated alert fires.

Preferred approach:
- Derive active managers by combining manifest role + latest `handshake`/`status` events within a time window (default 30m, configurable).
- `bus_status` should surface both the list of active managers and warnings when the list is empty.
- Expose a `--max-manager-gap` flag to tune the heartbeat threshold.
