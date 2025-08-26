# Agents ↔ TEOF (Quick Guide)

**Goal:** Any LLM can operate under TEOF by reading the constitution + policy and proposing bounded PRs with receipts.

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
