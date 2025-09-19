# Agents ↔ TEOF (Quick Guide)

**Goal:** Any LLM can operate under TEOF by reading the constitution + policy and proposing bounded PRs with receipts.

Treat this page as the day-to-day companion to the lightweight onboarding entry point (`.github/AGENT_ONBOARDING.md`). For the step-by-step coordination loop, defer to `docs/parallel-codex.md`.

## Quick Links
- List the current high-traffic surfaces: `python -m tools.agent.doc_links list`.
- Fetch one entry by id (e.g. `workflow-architecture`): `python -m tools.agent.doc_links show workflow-architecture`.
- Full manifest lives in `docs/quick-links.md`.
- Need machine-readable output? `python -m tools.agent.doc_links list --format json`.
- Need a manual receipt scaffold? `python -m tools.receipts.main scaffold plan --plan-id <id> --agent <id>` or `... claim --task <id> --agent <id>` creates the default files without touching plans/claims.

## Coordination (multi-agent)
> **Optional role module:** See [`docs/roles.md`](docs/roles.md) + `agents/roles.json` for a lightweight four-pillar breakdown (strategist, architect, automation engineer, risk sentinel). Pick a hat at session start or prune/replace the list to fit your crew. The roles are additive; delete the files if you prefer the classic free-form model.

## Idle Cadence
- Within 5 minutes of going idle, publish a status event and mirror it on the queue (`docs/parallel-codex.md#follow-up-logging`, `docs/collab-support.md`). Escalate after 30 minutes if no claim lands.
- Keep `tools.agent.bus_watch` tailing to spot blockers, responding with `bus_message --type status` when you intervene. Add `--meta reviewer=<id>` when auditing.
- Start each session with `python -m tools.agent.session_boot --agent <id> --focus <role>` so the bus records your presence. The helper now runs `git fetch --prune && git pull --ff-only` before logging the handshake; use `--no-sync` to skip or `--sync-allow-dirty` if you intentionally keep local changes. Add `--with-status` to capture a `bus_status` summary receipt automatically, and run `session_boot --summary "session wrap" --focus idle` when you switch context.
- Use the manifest helper when swapping roles (`python -m tools.agent.manifest_helper session-save <label>` / `session-restore <label>`) and the idle pickup helper (`python -m tools.agent.idle_pickup list|claim`) to grab vetted backlog without manager involvement.
- Scaffold receipts early: `python -m tools.planner.cli new <slug> --summary "..." --scaffold` seeds `_report/agent/<id>/<plan>/` with `notes.md`, `actions.json`, `tests.json`, and `summary.json`. Managers can add `--scaffold` to `tools.agent.claim_seed` or `tools.agent.task_assign` to prep the same structure during handoff.
- Managers: append `--log-heartbeat` when running `python -m tools.agent.manager_report` so `bus_status` sees a fresh status event (tweak the message with `--heartbeat-summary`; add extra metadata via `--heartbeat-meta key=value` or the shortcut `--heartbeat-shift <label>`, all of which print alongside the timestamp in `bus_status --preset manager`).
- Automate heartbeat coverage with `python -m tools.agent.bus_heartbeat --dry-run`; by default it watches for manager gaps (30 min) and idle claims (4 h) and stores receipts under `_report/agent/<id>/apoptosis-004/alerts/` without touching the bus. Drop the `--dry-run` flag to emit `alert` events/messages when the monitor should page the team.
- When you post receipts and the tests are green, release the claim promptly and move to the next assignment unless the manager’s reply includes a `hold` tag or you detect a risky signal (missing receipts, flaky tests, governance/capsule work). Explicitly note those edge cases on the bus so they stay visible.
- Summaries and audits belong in receipts: run `python -m tools.agent.bus_status --preset support --agent <id>` to use the helper defaults (limit 20, `--active-only`, `--window-hours 6`) and store transcripts under `_report/agent/<id>/` for planner validation. Add `--json` when scripting or `--window-hours 0` when you need the full event log.
- Keep automation healthy—run `tools.agent.task_sync` after releasing a claim and `python -m tools.maintenance.prune_artifacts --dry-run` daily to archive stale plans into `_apoptosis/<stamp>/`.
- Before pushing, run `tools/agent/preflight.sh` and `python3 tools.planner.validate.py --strict` to satisfy the receipts directive logged in the manager report.

## Claim Seeding (Managers)
- Seed `_bus/claims/<task>.json` before broadcasting assignments so the downstream guard passes: `python -m tools.agent.claim_seed --task QUEUE-014 --agent codex-2 --plan 2025-09-18-claim-seed-docs --branch agent/codex-2/queue-014 --status paused` (run `--help` for optional flags like `--notes`). The helper mirrors `bus_claim` but lets a manager stage the claim while the seat is still vacant.
- The `bus_message` claim guard rejects assignment/status posts when a claim is missing or owned by someone else. Seed first, then run `python -m tools.agent.task_assign ...`; the assignment now auto-claims on behalf of the engineer, so they can start immediately. Use `--no-auto-claim` only when staging backlog slots without beginning work.
- Drop a short `python -m tools.agent.session_brief --task QUEUE-014` snippet into the assignment message so the engineer sees the seeded branch/plan context alongside the bus receipts.

## Contract
- **Read:** `governance/CHARTER.md`, `governance/policy.json`, optional `governance/objectives.yaml`.
- **Propose:** a unified diff within `allow_globs`, `diff_limit`, no renames/deletes.
- **Label:** PR with `bot:autocollab`.
- **Prove:** include an **OCERS receipt** (inputs, model, commit base, hash of diff) in PR body.
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
1) Map to **one OCERS trait**.
2) Demand **receipts** (observable failure it would catch) or keep **optional**.
3) Prefer **editor/git-level** hygiene over new runtimes.
4) Propose a **sunset** and **fallback**.
