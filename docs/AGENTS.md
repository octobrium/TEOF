# Agents ↔ TEOF (Quick Guide)

**Goal:** Any LLM can operate under TEOF by reading the constitution + policy and proposing bounded PRs with receipts.

For a hands-on checklist, see `.github/AGENT_ONBOARDING.md`. It links the manifest template, plan scaffold, and `tools/agent/runner.sh` helper.

## Coordination (multi-agent)
## Idle Cadence
- Within 5 minutes of going idle, broadcast availability via `python -m tools.agent.bus_event log --event status --summary "<id> idle; available for support" --task QUEUE-010 --plan 2025-09-18-collab-support` and mirror it with a `bus_message --task QUEUE-010 --type status`.
- Keep `python -m tools.agent.bus_watch --limit 20 --follow --window-hours 4` running; respond to blockers with `bus_message --type status` (add `--meta reviewer=<id>` when reviewing).
- If still idle after 30 minutes, escalate using `bus_message --task QUEUE-010 --meta escalation=needed`; stop advertising availability once a new claim is recorded.
- Follow the dedicated [Idle-Agent Collaboration Workflow](docs/collab-support.md) when assisting another agent so offers, support plans, and receipts stay linked to the owning task.

- Start each session with `python -m tools.agent.session_boot --agent <id>` to announce presence and detect peers.
- Claim tasks through the repo bus: `_bus/claims/<task>.json` via `python -m tools.agent.bus_claim claim ...`.
- Log progress events with `python -m tools.agent.bus_event log ...`; auditors can replay `_bus/events/events.jsonl`.
- Summarize active work using `python -m tools.agent.bus_status --limit 20 --agent codex-2 --active-only --since 2025-09-18T00:00:00Z`; the CLI trims events to the last 24 hours by default (`--window-hours 0` disables) and `--json` helps when automations need machine-readable output. For live coordination, run `python -m tools.agent.bus_watch --limit 20 --follow` (add filters like `--agent codex-1 --event status --since 2025-09-17T23:00:00Z`; pass `--window-hours 0` when you need older history) and store receipts under `_report/agent/<id>/` so CI can verify plan references. Before opening PRs, run `tools/agent/preflight.sh` to catch missing receipts or plan issues locally.

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
