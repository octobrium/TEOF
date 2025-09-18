# Bus Messages

Purpose: structured agent-to-agent communication. Messages are stored as JSONL files under `_bus/messages/` and scoped per task or topic.

## Directory layout
- `_bus/messages/<task_id>.jsonl` — append-only log of coordination messages for a task (assignments, status pings, reviews).
- `_bus/messages/manager-report.jsonl` — optional high-level manager broadcasts.

## Message schema
Each line is a JSON object with required fields:

```json
{
  "ts": "2025-09-18T00:00:00Z",
  "from": "codex-1",
  "type": "assignment",
  "task_id": "QUEUE-001",
  "summary": "Assigned to codex-2 with plan 2025-09-17-agent-bus-watch",
  "branch": "agent/codex-2/queue-001",
  "receipts": ["_report/agent/codex-2/agent-bus-watch/pytest.json"],
  "meta": {"role": "engineer"}
}
```

`type` may be `assignment`, `status`, `request`, `note`, `consensus`, or `summary`. Additional fields may be included under `meta`.

Messages must be appended chronologically; CI validates structure and timestamps.

## Usage pattern
1. Manager assigns work via `tools/agent/task_assign.py`, which appends an `assignment` message.
2. Engineers reply with `status` or `note` messages indicating progress.
3. Manager posts a `consensus` or `summary` message prior to requesting human review.

This keeps agent communication auditable and tied to plans/receipts.
