# TEOF Agent Coordination Bus

Purpose: Provide a repo-native coordination lane for multiple agents (Codex sessions) to self-delegate work, emit status events, and avoid task collisions. The bus is auditable, append-only, and CI-enforced.

## Layout

- `_bus/claims/` — one JSON file per claimed task (`<task_id>.json`). Holds the current owner, branch, and timestamps. Only one claim file per task is permitted.
- `_bus/assignments/` — manager-authored assignment descriptors tying tasks to engineers.
- `_bus/events/events.jsonl` — append-only log of agent events (handshakes, claims, proposals, PRs, audits). Each line is a JSON object.
- `_bus/messages/` — task-scoped JSONL channels for richer coordination messages.
- `_bus/meta/agents.json` *(optional)* — registry of known agents (mirrors `AGENT_MANIFEST.json` entries) for quick lookup.

## Claim file schema (`_bus/claims/<task_id>.json`)

```json
{
  "task_id": "QUEUE-001",
  "plan_id": "2025-09-19-queue-001",
  "agent_id": "codex-1",
  "branch": "agent/codex-1/queue-001",
  "claimed_at": "2025-09-19T17:45:00Z",
  "status": "active",
  "notes": "Investigating queue hygiene edge cases"
}
```

- `status`: `active | paused | released | done`.
- `plan_id`: optional but recommended (ties to `_plans/*.plan.json`).

## Event log schema (`_bus/events/events.jsonl`)

Each line must be valid JSON with at least these fields:

```json
{"ts":"2025-09-19T17:50:10Z","agent_id":"codex-1","event":"proposal","task_id":"QUEUE-001","summary":"Drafted plan"}
```

Recommended fields: `branch`, `plan_id`, `pr`, `receipts`.

## CI invariants

- Claim filename must match `task_id` and be unique.
- Only one active claim per task.
- JSON must validate against schema; timestamps are ISO8601 `Z`.
- Event log must be append-only and valid JSONL.

## Tooling (planned)

- `python -m tools.agent.bus_claim` — create/release claims safely.
- `python -m tools.agent.bus_event` — append events with validation.
- `python -m tools.agent.bus_status` — render current claims + latest events (`--agent <id>`, `--active-only`, `--json`).
- `python -m tools.agent.bus_watch` — stream or filter events (`--follow`, `--since <ISO>`, `--agent <id>`, `--event <type>`).

## Workflow

1. Agent starts session and logs a handshake (`python -m tools.agent.session_boot --agent <id>`).
2. Manager assigns tasks with `python -m tools.agent.task_assign --task ... --engineer ...` (writes `_bus/assignments/<task>.json` and appends `_bus/messages/<task>.jsonl`).
3. Engineer claims assigned task (`bus_claim claim --task QUEUE-001 --plan ...`).
4. Engineer emits events during work (`bus_event log --event proposal ...`); manager monitors with `bus_watch` and `bus_status`.
5. Engineers update plan + justification, open PRs, and store receipts under `_report/agent/<id>/...`.
6. Manager runs `python -m tools.agent.manager_report` to generate `_report/manager/manager-report-<ts>.md` summarising consensus and outstanding work.
7. On completion, engineer releases claim (`bus_claim release ... --status done`), manager posts a `consensus` message if ready for review.
8. Humans audit via `_bus/events/*.jsonl`, `_bus/messages/*.jsonl`, and `_report/**` receipts.

## Interaction with memory + plans

- Claims reference `plan_id`; plans may include `links` pointing back to `_bus/claims/...`.
- Memory entries include the branch and cite `_bus/events/...` receipts.

By keeping coordination in-repo, multiple Codex instances can collaborate safely without extra infrastructure.
