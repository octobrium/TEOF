# Parallel Codex Playbook

Purpose: coordinate multiple Codex sessions (or other agents) working on TEOF in parallel without stepping on one another.

## Branch & Manifest Discipline

- Every agent works under `agent/<agent_id>/*` branches. Generate `agent_id` inside `AGENT_MANIFEST.json`.
- Each session keeps a dedicated manifest copy (e.g., `AGENT_MANIFEST.codex-2.json`) and symlinks/swaps it before running if needed.
- Tokens must be least-privilege (fine-grained PAT or GitHub App) scoped to those branches.

## Coordination Bus

- Use `_bus/claims/` to claim tasks (`tools/agent/bus_claim.py claim --task QUEUE-001`).
- Agents log progress to `_bus/events/events.jsonl` via `tools/agent/bus_event.py log ...`.
- Claims reference planner artifacts (set `--plan` to `_plans/<id>.plan.json`).
- Release claims with `bus_claim release --task QUEUE-001 --status done`.
- CI ensures one active claim per task and validates event JSON.

## Suggested Session Loop

1. **Sync** (`git pull origin main`).
2. **Announce session** (`python -m tools.agent.session_boot --agent <id>` to log a handshake + view peers).
3. **Managers assign tasks** (`python -m tools.agent.task_assign --task <id> --engineer <id> --plan <plan>`); engineers acknowledge with a `bus_event` status.
4. **Review queue** (`queue/`, `_bus/claims/`, `_bus/messages/`, `_bus/events/`).
5. **Claim** a task with `tools/agent/bus_claim.py claim ...` (engineer role) and keep `bus_watch` open for coordination.
6. **Plan** modifications under `_plans/` + justification.
7. **Implement** changes on `agent/<id>/<slug>` branch, storing receipts under `_report/agent/<id>/` and `_report/runner/` as needed.
8. **Log events** (`bus_event log --event proposal`, `--event pr_opened`) and append message responses via `bus_event` or JSONL entries.
9. **Open draft PR** with plan, justification, receipts.
10. **Managers run reports** (`python -m tools.agent.manager_report`) to produce `_report/manager/manager-report-<timestamp>.md` and post `consensus` messages when ready for human review.
11. **Release** claim once merged/closed and optionally refresh handshake (`session_boot --summary "session wrap"`).

## Self-Audit & Cross-Audit

- Use `tools/agent/bus_status.py --limit 20 --agent <id> --active-only` to summarise active claims and latest events (add `--json` when piping into dashboards).
- For a live feed while working, run `python -m tools.agent.bus_watch --limit 20 --follow`; add `--agent <id>` or `--event status` to focus the stream, or `--since <ISO>` to replay a window.
- Store receipts for these events under `_report/agent/<agent-id>/` (and `_report/runner/`, `_report/planner/` when applicable) so planner plans and CI can resolve them without manual copying.
- Encourage agents to emit `--extra reviewer=<agent>` or `event=audit` entries when they review a peer’s plan or PR.
- Reference `_bus/events/…` receipts in `memory/log.jsonl` entries to tie automation to human approvals.

## Failure Modes & Recovery

- If two agents grab the same task simultaneously, CI fails with duplicate claim error; resolve by releasing one claim.
- If an agent crashes mid-task, another agent may set `status=paused` with notes, then reclaim after confirming state.
- Event log is append-only; if corruption occurs, restore from history before merging further PRs.

## Recommended Labels & Metadata

- GitHub Issues: `codex::docs`, `codex::tests`, `codex::refactor` to signal preferred agent.
- `_plans` `links` field: add `{ "type": "bus", "ref": "_bus/claims/QUEUE-001.json" }` for easy traceability.

Following this playbook keeps parallel Codex sessions deterministic, auditable, and low-friction.
