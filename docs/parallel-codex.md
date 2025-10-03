# Parallel Codex Playbook

Purpose: coordinate multiple Codex sessions (or other agents) working on TEOF in parallel without stepping on one another. For the lightweight onboarding entry point use `.github/AGENT_ONBOARDING.md`; this playbook is the canonical reference once you enter the loop. Quick index: `python -m tools.agent.doc_links list` or `python -m tools.agent.doc_links show <id>` (manifest: `docs/quick-links.md`).

## Branch & Manifest Discipline

- Every agent works under `agent/<agent_id>/*` branches. Generate `agent_id` inside `AGENT_MANIFEST.json`.
- Each session keeps a dedicated manifest copy (e.g., `AGENT_MANIFEST.codex-2.json`) and symlinks/swaps it before running if needed. Sample manifests now live under `docs/examples/agents/`; copy one into the repo root as `AGENT_MANIFEST.json` (or symlink) before swapping seats. `session_boot` now refuses to run if the manifest agent disagrees with `--agent` unless you pass `--allow-manifest-mismatch`, in which case a warning is logged under `_report/agent/<id>/session_guard/`.
- Tokens must be least-privilege (fine-grained PAT or GitHub App) scoped to those branches.

## Coordination Bus

- Use `_bus/claims/` to claim tasks (`tools/agent/bus_claim.py claim --task QUEUE-001`).
- Agents log progress to `_bus/events/events.jsonl` via `tools/agent/bus_event.py log ...`.
- Claims reference planner artifacts (set `--plan` to `_plans/<id>.plan.json`).
- Release claims with `bus_claim release --task QUEUE-001 --status done`.
- CI ensures one active claim per task and validates event JSON.

> **Hub quick commands (manager-report)**
>
> | Action | Command |
> | --- | --- |
> | Announce presence | `python -m tools.agent.bus_message --task manager-report --type status --summary "<agent-id> online; focus=<role>" --meta agent=<agent-id>` |
> | Tail the hub | `python -m tools.agent.bus_watch --task manager-report --follow --limit 20` |
> | Claim work | `python -m tools.agent.bus_claim claim --task <task_id> --plan <plan_id>` |
> | Send heartbeat | `python -m tools.agent.bus_event log --event status --task <task_id> --summary "<agent-id> working" --plan <plan_id>` |
> | Heartbeat shortcut | `python -m tools.agent.bus_ping --task <task_id> --message-task <task_id> --summary "working"` |
> | Reply in-thread | `python -m tools.agent.bus_message --task <task_id> --type status --summary "<update>" --receipt <path>` |

Onboarding surfaces (`.github/AGENT_ONBOARDING.md` and `docs/AGENTS.md`) reuse the same commands so every new seat can confirm access to the coordination bus before picking up work.

**Guardrail:** `tools.agent.bus_message` refuses mismatched agent ids—run `python -m tools.agent.session_boot --agent <id>` (or `python -m tools.agent.manifest_helper activate <id>`) before posting so the manifest matches the seat you’re representing.

<a id="session-loop"></a>
## Suggested Session Loop

1. **Sync** (`git pull origin main`).
   - Start with `git status -sb`. If you inherit uncommitted changes from another seat, treat them as theirs—do **not** stash/reset. Run `python -m tools.agent.session_boot --agent <id> --sync-allow-dirty` so the handshake lands without touching their work; the helper now captures a `_report/session/<id>/dirty-handoff/` receipt and logs an `observation` event automatically. Add a quick `bus_event status` if you need extra context for the owner. If the edits block your task, escalate on the bus or draft a queue follow-up rather than mutating their branch. Session boot now also checks the current branch—stick to `agent/<id>/*` (or `main`) or pass `--allow-branch-mismatch` if you truly need to operate elsewhere; overrides still log a warning receipt.
2. **Announce session** (`python -m tools.agent.session_boot --agent <id> --focus <role>` logs a handshake, auto-syncs the repo, and now captures a coord_dashboard snapshot under `_report/agent/<id>/session_boot/`). Add `--with-status` if you also want a `bus_status` receipt, or `--no-dashboard` when you explicitly need to skip the dashboard snapshot. Pair it with `python -m tools.agent.manifest_helper session-save <label>` before you swap seats—`session-save` emits a status heartbeat automatically, so append `--heartbeat-meta shift=<label>` to tag the broadcast or `--no-heartbeat` if you truly need to skip it.
   - If you draft a fresh plan, run `python -m tools.planner.cli new <slug> --summary "..." --scaffold` so the corresponding `_report/agent/<id>/<plan>/` folder is ready before the first commit. Managers can mirror this with `tools.agent.claim_seed --scaffold` or `tools.agent.task_assign --scaffold` when staging handoffs.
3. **Managers assign tasks** (`python -m tools.agent.task_assign --task <id> --engineer <id> --plan <plan>`). Claims are created automatically for the assignee; add `--no-auto-claim` if you need to stage the backlog without starting the work immediately. Engineers should still acknowledge with a quick `bus_event` status.
4. **Review queue** (`queue/`, `_bus/claims/`, `_bus/messages/`, `_bus/events/`).
   - The coordination dashboard includes a **Dirty Handoffs** section—clear your agent’s entry (or reassign) before calling the board green.
5. **Heartbeat check** run `python -m tools.agent.bus_heartbeat --manager-window 30 --dry-run` to capture a receipt and confirm automation coverage. The helper records stale manager or idle-claim alerts under `_report/agent/<id>/apoptosis-004/alerts/`. When you need an interactive snapshot, `python -m tools.agent.bus_status --preset manager --manager-window 30` still surfaces the warning—follow up with a manager handshake or escalation in `manager-report` if either path flags a gap. The coordination dashboard now prints the active heartbeat windows and lists any in-flight automation plans (`Heartbeat automation in flight`) so you can tell whether codex-2/3/4 have shipped the auto hook, docs, and receipts before declaring the board green. Retired personas (e.g., dormant observers) are listed in `tools.agent.coord_dashboard.RETIRED_AGENTS` so they do not block the board; add/remove entries there when parking or reviving an agent. **Every time you open a new coordination thread (e.g., `BUS-COORD-xxxx`), run `python -m tools.agent.directive_pointer --task BUS-COORD-xxxx --summary "<directive summary>"`** so the pointer lands in `manager-report`. If the pointer is missing, automation will fail the plan in review.
6. **Claim / pick up** — auto-claim covers common assignments, but engineers can:
   - run `python -m tools.agent.idle_pickup list` to view unclaimed backlog items, or `... claim --task <id>` to auto-assign themselves when idle;
   - re-run `tools/agent/bus_claim.py claim ...` to reclaim stalled work, switch branches, or update status. Keep `bus_watch` open for coordination either way.
   - When receipts + tests are green, release the claim within minutes and move forward unless a `hold` note appears on the bus or you spot a risky signal (missing receipts, flaky tests, governance/capsule touchpoints). Flag those cases explicitly so the manager can weigh in.
7. **Plan** modifications under `_plans/` + justification. Reference only receipts that already live in git (`tools.planner.validate --strict` now rejects missing/ignored files).
8. **Implement** changes on `agent/<id>/<slug>` branch, storing receipts under `_report/agent/<id>/` and `_report/runner/` as needed.
9. **Log events** (`bus_event log --event proposal`, `--event pr_opened`) and append message responses via `bus_event` or JSONL entries.
10. **Open draft PR** with plan, justification, receipts.
11. **Managers run reports** (`python -m tools.agent.manager_report --log-heartbeat --heartbeat-shift <label>`, `python -m tools.agent.coord_dashboard report`) to produce `_report/manager/manager-report-<timestamp>.md`, emit a fresh heartbeat, and capture a coordination snapshot for follow-up triage. `bus_status --preset manager` now surfaces the heartbeat summary + metadata alongside the timestamp, so use `--heartbeat-shift` (or additional `--heartbeat-meta key=value`) to broadcast context like `shift=mid` or `cadence=daily`. The dashboard view has become the default “source of truth” during sweeps, so stash the generated receipt with any bus follow-ups.
12. **Run preflight** (`tools/agent/preflight.sh`) to ensure receipts and plans are valid before opening/refreshing the PR.
13. **Release** claim once merged/closed and optionally refresh handshake (`session_boot --summary "session wrap" --focus idle`). Capture a short reflection (`_report/agent/<id>/reflections/<date>.md`) on what worked, what stalled, and any nudges for the next session—the receipts become training data for future automation. Keep reflections there to avoid convenience creep scattering them across docs/ surfaces.

<a id="self-audit"></a>
## Self-Audit & Cross-Audit

- Use `python -m tools.agent.bus_heartbeat --dry-run` to produce an auditable alert receipt; add `--manager-window 30 --agent-window 240` (defaults) or tighten/disable windows per session. Combine with `--no-bus-event --no-bus-message` during rehearsals. As the automation plans land, expect the dashboard heartbeat note to shrink once the auto hook takes over routine beats.
- Use `tools/agent/bus_status.py --preset support --agent <id>` to summarise active claims and latest events (add `--json` when piping into dashboards or `--summary` for a compact bullet list).
- For a live feed while working, run `python -m tools.agent.bus_watch --limit 20 --follow`; add `--agent <id>` or `--event status` to focus the stream, or `--since <ISO>` to replay a window.
- Generate an evidence snapshot with `python -m tools.agent.receipts_index --output receipts-index.jsonl` before handing off; inspect the JSONL to spot missing or untracked receipts across plans and manager messages.
- Track how fast reflections turn into evidence with `python -m tools.agent.receipts_metrics --output receipts-latency.jsonl`; review the per-plan latency deltas and address outliers.
- Run `python -m tools.agent.session_brief --task <id> --preset operator --output _report/agent/<id>/session_brief/operator.json` to emit the Operator Mode checklist (manager tail, plan validation, quickstart receipts, claim seed, task sync, receipts index) as a receipt.
- Store receipts for these events under `_report/agent/<agent-id>/` (and `_report/runner/`, `_report/planner/` when applicable) so planner plans and CI can resolve them without manual copying.
- Encourage agents to emit `--extra reviewer=<agent>` or `event=audit` entries when they review a peer’s plan or PR.
- Reference `_bus/events/…` receipts in `memory/log.jsonl` entries to tie automation to human approvals.

### Maintenance Helpers

- Quick-links index: `python -m tools.agent.doc_links list` (or `show <id>`, add `--format json` when scripting) surfaces governance/onboarding hotspots without manual searching. Receipts for doc link updates live alongside `docs/quick-links.{json,md}` and the helper’s pytest log.
- Plan hygiene: `python -m tools.maintenance.plan_hygiene --check` highlights status-enum drift; add `--apply` when you’re ready to normalise in place. The helper records before/after diffs plus pytest/planner receipts in `_report/agent/<id>/plan-hygiene/`.

<a id="follow-up-logging"></a>
## Follow-up Logging

- When a manager posts coordination requests (e.g., reminding an engineer to release a claim), follow up with `python -m tools.agent.bus_event log --event status --summary "<agent> handled <follow-up>" --plan <plan-id> --receipt <path>` so the resolution lands in `_bus/events/events.jsonl` with a receipt.
- Mirror the update on the relevant bus message thread (task-specific file or `manager-report.jsonl`) using `python -m tools.agent.bus_message --task <id> --type status --summary "<agent> resolved follow-up" --receipt <path>`.
- File the referenced receipt under `_report/agent/<agent-id>/...` with the command output (task sync logs, pytest transcripts, etc.) so future plans and CI runs can verify the action without guessing.
- Add a short note in the plan or handoff summary pointing to the bus entries when the follow-up closes. This creates a deterministic breadcrumb trail before consensus queues (QUEUE-030..033) go live.

## Coordination Dashboard

- Generate an aggregate snapshot with `python -m tools.agent.coord_dashboard report`. Default format is Markdown; add `--format json` for automation workflows.
- Outputs land in `_report/manager/coordination-dashboard-<timestamp>.{md,json}` (use `--output` to override). Store the receipt when logging manager follow-ups.
- Summaries include active plans, live claims, heartbeat health, and the latest manager directives with alerts for stale/missing signals.
- Pair the dashboard with `manager_report` during cadence reviews so follow-up items have deterministic breadcrumbs.

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
