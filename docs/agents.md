# Agents ↔ TEOF (Quick Guide)

**Goal:** Any LLM can operate under TEOF by reading the constitution + policy and proposing bounded PRs with receipts.

Treat this page as the day-to-day companion to the lightweight onboarding entry point (`.github/AGENT_ONBOARDING.md`). For the step-by-step coordination loop, defer to `docs/parallel-codex.md`.

## Quick Links
- List the current high-traffic surfaces: `python -m tools.agent.doc_links list`.
- Fetch one entry by id (e.g. `workflow-architecture`): `python -m tools.agent.doc_links show workflow-architecture`.
- Full manifest lives in `docs/quick-links.md`.
- Need machine-readable output? `python -m tools.agent.doc_links list --format json`.
- Need a manual receipt scaffold? `python -m tools.receipts.main scaffold plan --plan-id <id> --agent <id>` or `... claim --task <id> --agent <id>` creates the default files without touching plans/claims.
- Canonical core map: `governance/core/index.md`.
- Persistent lane primer + helper CLI: see `docs/automation/agent-lane.md` and `python -m tools.agent.lane --help`.

## Communication Quickstart (manager-report hub)
- **Verify manifest** – confirm `AGENT_MANIFEST.json` (or `python3 -m tools.agent.manifest_helper show`) lists the `agent_id` you will broadcast with.
- **Announce the session** – `python3 -m tools.agent.session_boot --agent <agent-id> --focus <role> --with-status` records the handshake, ensures the repo is synced, and captures a `bus_status` receipt.
- **Read the hub** – the same `session_boot` run tails `_bus/messages/manager-report.jsonl` and stores `_report/session/<agent-id>/manager-report-tail.txt`. Preflight fails fast without this receipt, so treat it as evidence you checked the coordination lane.
- **Broadcast the hello** – post to the shared lane with `python3 -m tools.agent.bus_message --task manager-report --type status --summary "<agent-id>: on deck for <focus>" --note "Context"`. Keep the `<agent-id>:` prefix so downstream readers know who spoke.
- **Respect the guard** – `tools.agent.bus_message` exits when the manifest and `--agent` disagree; rerun `session_boot` or `python3 -m tools.agent.manifest_helper activate <id>` before posting.
- **Watch the feed** – keep `python3 -m tools.agent.bus_watch --task manager-report --follow --limit 20` running (or spot-check via `python3 -m tools.agent.session_brief --task manager-report --limit 5`).
- **Coordinate ongoing work** – claim tasks (`python3 -m tools.agent.bus_claim claim --task <task_id> --plan <plan_id>`), emit heartbeats (`python3 -m tools.agent.bus_event log --event status ...`), and reply on `_bus/messages/<task>.jsonl` (`python3 -m tools.agent.bus_message --task <task_id> --type status ... --receipt <path>`), attaching receipts whenever possible.
- **Heartbeat shortcut** – `python3 -m tools.agent.bus_ping --task <task_id> --message-task <task_id> --summary "progress"` auto-prefixes `<agent-id>:` and logs both the event + message. Add `--skip-message` when you only need the event log.

## Operator Mode Checklist (refine TEOF safely)
- **Confirm placement** – compare the repo layout against `docs/architecture.md`; queue architecture fixes first if folders drift.
- **Re-run the quickstart** – execute `docs/quickstart.md` commands, capture receipts, and log an updated plan in `_plans/` (`python3 -m tools.planner.cli new ...` + `python3 tools/planner/validate.py`).
- **Verify guards** – ensure `scripts/policy_checks.sh` (import policy + quickstart smoke) is wired in CI; note gaps if enforcement is missing.
- **Patch observed gaps** – propose the smallest changes that make quickstart, docs, or imports accurate again. Document receipts under `_report/agent/<id>/...`.
- **Publish the next steps** – surface a prioritized list (3–6 items) in your plan so other agents can resume the refinement loop.
- **Seed and sync claims** – run `python3 -m tools.agent.claim_seed --task <id> --agent <owner> --plan <plan-id>` before assignments, and `python3 -m tools.agent.task_sync` after releasing work so `agents/tasks/tasks.json` stays current.
- **Escalate deliberately** – only when workflow rules prevent progress, draft a proposal in `docs/proposals/` and, if needed, a Meta-TEP (see `docs/workflow.md#dna-recursion-self-improvement-of-the-rules`) before editing the DNA docs.
- **Capture the checklist** – run `python3 -m tools.agent.session_brief --task <queue-id> --preset operator --output _report/agent/<id>/session_brief/operator.json` to emit a JSON receipt showing which prerequisites (manager tail, plan validation, quickstart receipts, claim seed, task sync, receipts index) still need attention.

### Example session transcript
```
$ python3 -m tools.agent.manifest_helper show
$ python3 -m tools.agent.session_boot --agent codex-4 --focus docs --with-status
$ python3 -m tools.agent.bus_message --task manager-report --type status \
    --summary "codex-4: online; focus=docs"
$ python3 -m tools.agent.session_brief --task manager-report --limit 5
$ python3 -m tools.agent.bus_claim claim --task QUEUE-123 --plan 2025-09-20-queue-123
$ python3 -m tools.agent.bus_event log --event status --task QUEUE-123 \
    --summary "codex-4 working" --plan 2025-09-20-queue-123
$ python3 -m tools.agent.bus_message --task QUEUE-123 --type status \
    --summary "codex-4: uploaded receipts" --receipt _report/agent/codex-4/queue-123/notes.md
```

### Bootstrap (one minute)
<!-- generated: quickstart snippet -->
Run this smoke test on a fresh checkout:
```bash
python3 -m pip install -e .
teof brief
ls artifacts/systemic_out/latest
cat artifacts/systemic_out/latest/brief.json
```

- Install exposes the teof console script.
- teof brief scores docs/examples/brief/inputs/ and writes receipts under artifacts/systemic_out/<UTC>.



## Coordination (multi-agent)
> **Optional role module:** See [`docs/roles.md`](docs/roles.md) + `agents/roles.json` for a lightweight four-pillar breakdown (strategist, architect, automation engineer, risk sentinel). Pick a hat at session start or prune/replace the list to fit your crew. The roles are additive; delete the files if you prefer the classic free-form model.

## Idle Cadence
- Within 5 minutes of going idle, publish a status event and mirror it on the queue (`docs/parallel-codex.md#follow-up-logging`, `docs/collab-support.md`). Escalate after 30 minutes if no claim lands.
- Keep `tools.agent.bus_watch` tailing to spot blockers, responding with `bus_message --type status` when you intervene. Add `--meta reviewer=<id>` when auditing.
- Start each session with `python -m tools.agent.session_boot --agent <id> --focus <role>` so the bus records your presence. The helper now runs `git fetch --prune && git pull --ff-only` before logging the handshake, emits a coord_dashboard snapshot under `_report/agent/<id>/session_boot/`, **and** writes `_report/session/<id>/manager-report-tail.txt` so you prove you read the hub. Use `--no-sync` to skip the fetch/pull, `--sync-allow-dirty` if you intentionally keep local changes, `--with-status` for a `bus_status` summary receipt, or `--no-dashboard` if you truly need to skip the dashboard capture. Close the loop with `session_boot --summary "session wrap" --focus idle` when you switch context.
- Use the manifest helper when swapping roles (`python -m tools.agent.manifest_helper session-save <label>` / `session-restore <label>`). `session-save` now records a status heartbeat automatically—add `--heartbeat-meta shift=<label>` (or similar) to annotate the broadcast or `--no-heartbeat` if you need a silent snapshot. Pair this with the idle pickup helper (`python -m tools.agent.idle_pickup list|claim`) to grab vetted backlog without manager involvement.
- Scaffold receipts early: `teof-plan new <slug> --summary "..." --scaffold` (or `python -m tools.planner.cli new ...`) seeds `_report/agent/<id>/<plan>/` with `notes.md`, `actions.json`, `tests.json`, and `summary.json`. Managers can add `--scaffold` to `tools.agent.claim_seed` or `tools.agent.task_assign` to prep the same structure during handoff.
- Managers: append `--log-heartbeat` when running `python -m tools.agent.manager_report` so `bus_status` sees a fresh status event (tweak the message with `--heartbeat-summary`; add extra metadata via `--heartbeat-meta key=value` or the shortcut `--heartbeat-shift <label>`, all of which print alongside the timestamp in `bus_status --preset manager`).
- Automate heartbeat coverage with `python -m tools.agent.bus_heartbeat --dry-run`; by default it watches for manager gaps (30 min) and idle claims (4 h) and stores receipts under `_report/agent/<id>/apoptosis-004/alerts/` without touching the bus. Drop the `--dry-run` flag to emit `alert` events/messages when the monitor should page the team. While the codex-2/3/4 heartbeat plans are in flight, the coordination dashboard's heartbeat section calls out the active windows and the automation rollout so you know when the auto hook replaces the manual invocations.
- When you retire a persona, add its id to `tools.agent.coord_dashboard.RETIRED_AGENTS` (and note the retirement in your session brief) so the dashboard stops expecting new heartbeats until it returns.
- When you post receipts and the tests are green, release the claim promptly and move to the next assignment unless the manager’s reply includes a `hold` tag or you detect a risky signal (missing receipts, flaky tests, governance/capsule work). Explicitly note those edge cases on the bus so they stay visible.
- Prefix bus summaries with your `agent_id` (`<agent-id>:`) so manager-report, manifests, and receipts stay aligned.
- Summaries and audits belong in receipts: run `python -m tools.agent.bus_status --preset support` to use the helper defaults (limit 20, `--active-only`, `--window-hours 6`). The command now automatically targets the agent in `AGENT_MANIFEST.json`; pass `--agent <id>` when you need to inspect another seat. Store transcripts under `_report/agent/<id>/` for planner validation. Add `--json` when scripting or `--window-hours 0` when you need the full event log.
- Keep automation healthy—run `tools.agent.task_sync` after releasing a claim and `python -m tools.maintenance.prune_artifacts --dry-run` daily to archive stale plans into `_apoptosis/<stamp>/`.
- When you publish a new coordination directive (`BUS-COORD-xxxx`), run `python -m tools.agent.directive_pointer --task BUS-COORD-xxxx --summary "<directive summary>" --plan <plan-id>` so the helper writes the directive entry **and** mirrors a pointer in `manager-report`. Add `--pointer-summary/--pointer-note` if you need custom manager wording; plans that skip the pointer still fail review.
- Before pushing, run `tools/agent/preflight.sh` and `python3 tools/planner/validate.py --strict --output _report/planner/validate/summary-latest.json` — this keeps the validator receipt stable so plans reference a file guaranteed to exist in the repo.

## Claim Seeding (Managers)
- Seed `_bus/claims/<task>.json` before broadcasting assignments so the downstream guard passes: `python -m tools.agent.claim_seed --task QUEUE-014 --agent codex-2 --plan 2025-09-18-claim-seed-docs --branch agent/codex-2/queue-014 --status paused` (run `--help` for optional flags like `--notes`). The helper mirrors `bus_claim` but lets a manager stage the claim while the seat is still vacant.
- The `bus_message` CLI now enforces the claim guard: it exits if the task lacks a claim, belongs to another agent, or has been released. Seed first, then run `python -m tools.agent.task_assign ...`; the assignment now auto-claims on behalf of the engineer, so they can start immediately. Use `--no-auto-claim` only when staging backlog slots without beginning work.
- Drop a short `python -m tools.agent.session_brief --task QUEUE-014` snippet into the assignment message so the engineer sees the seeded branch/plan context alongside the bus receipts.

## Contract
- **Read:** `governance/CHARTER.md`, `governance/policy.json`, optional `governance/objectives.yaml`.
- **Propose:** a unified diff within `allow_globs`, `diff_limit`, no renames/deletes.
- **Label:** PR with `bot:autocollab`.
- **Prove:** include a **systemic receipt** (inputs, model, commit base, hash of diff) in PR body.
- **Pass:** required checks (`teof/fitness`, `guardrails/verify`) must be green.

## System prompt (canonical)
Maintainers export a canonical prompt via `bin/build-system-prompt` into `_report/system_prompt-<sha>.txt`.
Agents may fetch and use that as their **system** message.

## Safety
- No network/tool use beyond repo unless explicitly granted.
- Budgets must be respected (tokens/cost), see `policy.json`.

## Policy Anchors
- `governance/policy.json`
- `docs/workflow.md`
- `docs/architecture.md`

## Fitness (Stage F)
Before recommending any new tool/process:
1) Map to **primary systemic targets**.
2) Demand **receipts** (observable failure it would catch) or keep **optional**.
3) Prefer **editor/git-level** hygiene over new runtimes.
4) Propose a **sunset** and **fallback**.
