# Parallel Codex Playbook

Purpose: coordinate multiple Codex sessions (or other agents) working on TEOF in parallel without stepping on one another. For the lightweight onboarding entry point use `.github/AGENT_ONBOARDING.md`; this playbook is the canonical reference once you enter the loop. Quick index: `python -m tools.agent.doc_links list` (`docs/quick-links.md`).

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

<a id="session-loop"></a>
## Suggested Session Loop

1. **Sync** (`git pull origin main`).
2. **Announce session** (`python -m tools.agent.session_boot --agent <id> --focus <role>` logs a handshake + intent; add `--with-status` to grab an immediate bus summary receipt).
3. **Managers assign tasks** (`python -m tools.agent.task_assign --task <id> --engineer <id> --plan <plan>`). Claims are created automatically for the assignee; add `--no-auto-claim` if you need to stage the backlog without starting the work immediately. Engineers should still acknowledge with a quick `bus_event` status.
4. **Review queue** (`queue/`, `_bus/claims/`, `_bus/messages/`, `_bus/events/`).
5. **Heartbeat check** run `python -m tools.agent.bus_status --preset manager --manager-window 30` to confirm a manager heartbeat; if you see the warning, announce a manager handshake or escalate in `manager-report`.
6. **Claim / pick up** — auto-claim covers common assignments, but engineers can:
   - run `python -m tools.agent.idle_pickup list` to view unclaimed backlog items, or `... claim --task <id>` to auto-assign themselves when idle;
   - re-run `tools/agent/bus_claim.py claim ...` to reclaim stalled work, switch branches, or update status. Keep `bus_watch` open for coordination either way.
7. **Plan** modifications under `_plans/` + justification.
8. **Implement** changes on `agent/<id>/<slug>` branch, storing receipts under `_report/agent/<id>/` and `_report/runner/` as needed.
9. **Log events** (`bus_event log --event proposal`, `--event pr_opened`) and append message responses via `bus_event` or JSONL entries.
10. **Open draft PR** with plan, justification, receipts.
11. **Managers run reports** (`python -m tools.agent.manager_report`) to produce `_report/manager/manager-report-<timestamp>.md` and post `consensus` messages when ready for human review.
12. **Run preflight** (`tools/agent/preflight.sh`) to ensure receipts and plans are valid before opening/refreshing the PR.
13. **Release** claim once merged/closed and optionally refresh handshake (`session_boot --summary "session wrap" --focus idle`).

<a id="self-audit"></a>
## Self-Audit & Cross-Audit

- Use `tools/agent/bus_status.py --preset support --agent <id>` to summarise active claims and latest events (add `--json` when piping into dashboards or `--summary` for a compact bullet list).
- For a live feed while working, run `python -m tools.agent.bus_watch --limit 20 --follow`; add `--agent <id>` or `--event status` to focus the stream, or `--since <ISO>` to replay a window.
- Store receipts for these events under `_report/agent/<agent-id>/` (and `_report/runner/`, `_report/planner/` when applicable) so planner plans and CI can resolve them without manual copying.
- Encourage agents to emit `--extra reviewer=<agent>` or `event=audit` entries when they review a peer’s plan or PR.
- Reference `_bus/events/…` receipts in `memory/log.jsonl` entries to tie automation to human approvals.

<a id="follow-up-logging"></a>
## Follow-up Logging

- When a manager posts coordination requests (e.g., reminding an engineer to release a claim), follow up with `python -m tools.agent.bus_event log --event status --summary "<agent> handled <follow-up>" --plan <plan-id> --receipt <path>` so the resolution lands in `_bus/events/events.jsonl` with a receipt.
- Mirror the update on the relevant bus message thread (task-specific file or `manager-report.jsonl`) using `python -m tools.agent.bus_message --task <id> --type status --summary "<agent> resolved follow-up" --receipt <path>`.
- File the referenced receipt under `_report/agent/<agent-id>/...` with the command output (task sync logs, pytest transcripts, etc.) so future plans and CI runs can verify the action without guessing.
- Add a short note in the plan or handoff summary pointing to the bus entries when the follow-up closes. This creates a deterministic breadcrumb trail before consensus queues (QUEUE-030..033) go live.

## Consensus Toolkit (Preview)

- Use `python -m tools.consensus.ledger --format table` to inspect `_report/ledger.csv` with optional filters such as `--decision`, `--agent`, `--since`, and `--limit`.
- Capture JSON receipts with `--output <file>` (relative paths land in `_report/consensus/`) so consensus reviews can attach deterministic evidence.
- Append normalized receipts when closing decisions via `python -m tools.consensus.receipts --decision <id> --summary "..." --agent <id> --receipt <path>` or by adding `--consensus-decision <id>` to `python -m tools.agent.bus_event log ...`. Both paths write to `_report/consensus/`.
- Pair CLI runs with bus follow-up logs referencing the generated receipt to keep consensus bookkeeping auditable.
- Summarise open decisions with `python -m tools.consensus.dashboard --format table` (add `--task` filters or `--since` when needed). Escalate in `manager-report` if a decision shows zero receipts or the last update exceeds the 24h cadence.

## Consensus Cadence

- **Daily sweep (≤10 minutes):** the on-call agent tails `python -m tools.consensus.ledger --limit 5` and `python -m tools.consensus.dashboard --format table --since <24h>` to confirm fresh receipts. Log `python -m tools.agent.bus_event log --event status --consensus-decision <id>` for any decisions touched and capture output under `_report/agent/<id>/consensus/`.
- **Weekly review:** managers run the ledger + dashboard commands for the trailing week, capture a JSONL receipt via `python -m tools.consensus.receipts --decision WEEKLY-<iso>` and post a `bus_message --type consensus` summarising health.
- **Escalation path:** if a decision lacks receipts after 24h, issue `bus_message --type request --meta escalation=consensus` and assign follow-up before marking the weekly review complete.
- **Receipts:** keep daily sweep logs in `_report/agent/<id>/consensus/` and weekly summaries in `_report/manager/` so automation can enforce the cadence.

## Failure Modes & Recovery

- If two agents grab the same task simultaneously, CI fails with duplicate claim error; resolve by releasing one claim.
- If an agent crashes mid-task, another agent may set `status=paused` with notes, then reclaim after confirming state.
- Event log is append-only; if corruption occurs, restore from history before merging further PRs.

## Recommended Labels & Metadata

- GitHub Issues: `codex::docs`, `codex::tests`, `codex::refactor` to signal preferred agent.
- `_plans` `links` field: add `{ "type": "bus", "ref": "_bus/claims/QUEUE-001.json" }` for easy traceability.

Following this playbook keeps parallel Codex sessions deterministic, auditable, and low-friction.
