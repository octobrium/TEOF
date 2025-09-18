# Agents ↔ TEOF (Quick Guide)

**Goal:** Any LLM can operate under TEOF by reading the constitution + policy and proposing bounded PRs with receipts.

For a hands-on checklist, see `.github/AGENT_ONBOARDING.md`. It links the manifest template, plan scaffold, and `tools/agent/runner.sh` helper.

## Coordination (multi-agent)
- Start each session with `python -m tools.agent.session_boot --agent <id>` to announce presence and detect peers.
- Claim tasks through the repo bus: `_bus/claims/<task>.json` via `python -m tools.agent.bus_claim claim ...`.
- Log progress events with `python -m tools.agent.bus_event log ...`; auditors can replay `_bus/events/events.jsonl`.
- Summarize active work using `python -m tools.agent.bus_status --limit 20`. For live coordination, run `python -m tools.agent.bus_watch --limit 20 --follow` and add `--agent codex-1 --event status --since 2025-09-17T23:00:00Z` to focus on specific peers or windows.

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
