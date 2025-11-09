# Persistent Agent Lane (Handshake → Claim → Broadcast → Memory)

Status: Draft implementation guide  
Scope: L5 Workflow ↔ L6 Automation  
Systemic targets: Unity (S1) + Resilience (S4) by keeping every agent session observable and reversible.

## Why this lane exists

TEOF already defines **what** coordination must honor (observation-first, append-only receipts, single claims). This guide captures **how** to stand up a persistent lane so that every session produces the same traceable sequence:

1. **Handshake / Intake** – verify manifest + repo state, tail the manager feed, log `bus/events` entry.
2. **Claim / Resume** – ensure a task + plan anchor exists (create or refresh via `_plans/`), then claim through `_bus/claims/<task>.json`.
3. **Broadcast / Heartbeat** – emit structured status on `_bus/events/events.jsonl` and `_bus/messages/<task>.jsonl`, attaching receipts.
4. **Memory / Next steps** – append to `memory/log.jsonl`, stash receipts under `_report/agent/<id>/…`, and publish the next action in the plan.

Every phase already has tooling; the “lane” simply wires them together so autonomy ratchets upward by default.

## Manual lane (existing commands)

| Phase | Command(s) | Mandatory receipts |
| --- | --- | --- |
| Handshake | `python -m tools.agent.session_boot --agent <id> --focus <focus> --with-status` | `_report/session/<id>/session_boot/*.json` |
| Claim | `python -m teof bus_claim claim --task <queue-id> --plan <plan-id> [--branch …]` | `_bus/claims/<task>.json`, `_plans/<plan>.plan.json` |
| Broadcast | `python3 -m teof bus_event log --event status --task <task> --summary "..." --plan <plan>` and/or `python -m tools.agent.bus_ping …` | `_bus/events/events.jsonl`, `_bus/messages/<task>.jsonl` |
| Memory | `python tools/memory/log-entry.py --summary "…" --ref <task/plan> --artifact <receipt>` | `memory/log.jsonl`, `_report/agent/<id>/…` |

Running these in order already satisfies manager policies. The lane helper below packages the same choreography so new agents can plug in with fewer manual steps.

## Lane helper CLI

`python -m tools.agent.lane` performs the standard sequence (handshake → claim → broadcast) and drops a structured receipt under `_report/agent/<id>/lane/<UTC>.json`.

### Example

```bash
python -m tools.agent.lane \
  --agent codex-7 \
  --focus docs \
  --task QUEUE-204 \
  --plan 2025-11-07-queue-204 \
  --summary "codex-7 syncing status receipts" \
  --message-task manager-report
```

What happens:

1. `session_boot` runs with `--with-status`, refreshing the manager report receipt.
2. `python -m teof bus_claim` (optional) ensures the task is owned (`--skip-claim` bypasses this).
3. `python3 -m teof bus_event log` emits a status heartbeat (and optionally `bus_message` for a lane like `manager-report`).
4. `_report/agent/codex-7/lane/<ts>.json` records the arguments + exit codes so other agents can replay or audit.

### Flags

| Flag | Description |
| --- | --- |
| `--agent <id>` | Required agent id (must match `AGENT_MANIFEST`). |
| `--focus <focus>` | Optional focus string recorded in the handshake. |
| `--task <queue-id>` | Target task id; enables claim + event linkage. |
| `--plan <plan-id>` | Plan identifier recorded in claim + events. |
| `--branch <branch>` | Override branch name when claiming. |
| `--summary "<text>"` | Status summary broadcast during the heartbeat. |
| `--message-task <task>` | Also post to `_bus/messages/<task>.jsonl`. |
| `--skip-claim`, `--skip-event`, `--skip-handshake`, `--skip-message` | Disable individual phases (defaults run everything except message). |

Hand off to `python tools/memory/log-entry.py …` after the helper completes to keep the memory log append-only (automation hook forthcoming).

## Operational checklist

- Create/refresh the plan before claiming; the lane expects `_plans/<plan>.plan.json` to exist and validate.
- Ensure `_report/agent/<id>/lane/` is tracked—receipts from each run unlock fast forensic replay.
- During long sessions, rerun `python -m tools.agent.lane --skip-claim --message-task manager-report --summary "…"`.
- When releasing the task, run `python -m teof bus_claim release …` and capture a final lane receipt for the exit heartbeat.

This helper doesn’t replace the constitutional rules; it makes following them the default. Extend it (or compose new helpers) as additional phases become automatable (plan validation, memory append, receipts index refresh, etc.).
