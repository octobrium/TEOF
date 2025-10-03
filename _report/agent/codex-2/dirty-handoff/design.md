# Dirty Handoff Automation Design (2025-10-03)

## Goal
Automate the guardrail when `session_boot` aborts because the working tree has uncommitted changes. The helper should:

1. Persist a receipt under `_report/session/<agent>/dirty-handoff/` describing the git status snapshot so the originating agent can reconcile later.
2. Append a coordination bus event (`event=observation`) noting the dirty pickup, without requiring a task claim (so new seats can log before swapping manifests).
3. Surface the receipt path in terminal output so the current agent can attach it to a manual `bus_event` status if they want a richer summary.
4. Feed dirty-handoff alerts into the coordination dashboard so operators see them until someone clears the working tree.

## Receipt draft
- Location: `_report/session/<agent>/dirty-handoff/dirty-<timestamp>.txt`
- Contents:
  ```
  # dirty handoff
  # agent=<agent>
  # captured_at=<iso>
  # status_path=<relative path>
  <git status --short output>
  ```

## Event draft
- Append to `_bus/events/events.jsonl`
- Payload template:
  ```json
  {
    "ts": <iso>,
    "agent_id": <agent>,
    "event": "observation",
    "summary": "Dirty working tree detected during session_boot",
    "receipts": ["_report/session/<agent>/dirty-handoff/dirty-<timestamp>.txt"]
  }
  ```

## Dashboard hook
- Extend `tools.agent.coord_dashboard` to scan `_report/session/**/dirty-handoff/*.txt`
- Summarise per agent (latest timestamp + receipt path) under a new "Dirty Handoffs" section.

## Open questions
- Leave git status unchanged (yes; no cleanup).
- Coordination bus note per automation is enough? We may choose to keep it as `observation` so guards avoid claim checks.
- Clearing alert: agents delete/commit receipts once resolved; dashboard hides when directory empty.
