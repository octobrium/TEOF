# Agents ↔ TEOF (Quick Guide)

**Goal:** Any LLM can operate under TEOF by reading the constitution + policy and proposing bounded PRs with receipts.

For a hands-on checklist, see `.github/AGENT_ONBOARDING.md`. It links the manifest template, plan scaffold, and `tools/agent/runner.sh` helper.

## Coordination (multi-agent)
> **Optional role module:** See [`docs/roles.md`](docs/roles.md) + `agents/roles.json` for a lightweight four-pillar breakdown (strategist, architect, automation engineer, risk sentinel). Pick a hat at session start or prune/replace the list to fit your crew. The roles are additive; delete the files if you prefer the classic free-form model.

## Idle Cadence
- Within 5 minutes of going idle, broadcast availability via `python -m tools.agent.bus_event log --event status --summary "<id> idle; available for support" --task QUEUE-010 --plan 2025-09-18-collab-support` and mirror it with a `bus_message --task QUEUE-010 --type status`.
- Keep `python -m tools.agent.bus_watch --limit 20 --follow --window-hours 4` running; respond to blockers with `bus_message --type status` (add `--meta reviewer=<id>` when reviewing).
- If still idle after 30 minutes, escalate using `bus_message --task QUEUE-010 --meta escalation=needed`; stop advertising availability once a new claim is recorded.
- Follow the dedicated [Idle-Agent Collaboration Workflow](docs/collab-support.md) when assisting another agent so offers, support plans, and receipts stay linked to the owning task.

- Start each session with `python -m tools.agent.session_boot --agent <id>` to announce presence and detect peers.
- Use `python -m tools.agent.manifest_helper list` to view available manifest variants and `python -m tools.agent.manifest_helper activate AGENT_MANIFEST.<id>.json` when swapping roles; run `python -m tools.agent.manifest_helper restore` after the session to restore the last backup.
- Claims are created automatically when a manager assigns you work. Use `python -m tools.agent.idle_pickup list` to see open backlog items, and `python -m tools.agent.idle_pickup claim --task <id>` when you want to auto-assign yourself. Fall back to `_bus/claims/<task>.json` via `python -m tools.agent.bus_claim claim ...` only when you need to change branches or update status manually.
- Log progress events with `python -m tools.agent.bus_event log ...`; auditors can replay `_bus/events/events.jsonl`.
- Summarize active work using `python -m tools.agent.bus_status --limit 20 --agent codex-2 --active-only --since 2025-09-18T00:00:00Z`; the CLI trims events to the last 24 hours by default (`--window-hours 0` disables) and `--json` helps when automations need machine-readable output. For live coordination, run `python -m tools.agent.bus_watch --limit 20 --follow` (it defaults to the same 24-hour window; add filters like `--agent codex-1 --event status --since 2025-09-17T23:00:00Z` and pass `--window-hours 0` when you need older history) and store receipts under `_report/agent/<id>/` so CI can verify plan references. The command now reports active managers and warns when no manager heartbeat is detected within the `--manager-window` (default 30m); if you see the warning, escalate in `manager-report` or volunteer via `bus_event log --event handshake`. Before opening PRs, run `tools/agent/preflight.sh` to catch missing receipts or plan issues locally.
- After releasing a claim, run `python -m tools.agent.task_sync` to flip finished tasks to `status=done` and clear released ones back to `open`.
- Run the automated pruning sweep once a day: `python -m tools.maintenance.prune_artifacts --dry-run` (drop `--dry-run` after reviewing output). It archives stale plans/receipts into `_apoptosis/<stamp>/` so new agents boot quickly.

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

## Fitness (Stage F)
Before recommending any new tool/process:
1) Map to **one OCERS trait**.
2) Demand **receipts** (observable failure it would catch) or keep **optional**.
3) Prefer **editor/git-level** hygiene over new runtimes.
4) Propose a **sunset** and **fallback**.
