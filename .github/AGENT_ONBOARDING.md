# Agent Onboarding (TEOF)

Purpose: help a human + LLM pair plug into TEOF safely, with auditable micro-proposals and minimal privileges.

## Quick Loop

1. **Create a scoped credential.** Prefer a GitHub App or fine-grained PAT limited to `contents:read`. Only upgrade to `contents:write` for branches under `agent/<your-id>/*` after manual review. Never paste tokens into chat; store them locally (shell env, keychain, or agent config).
2. **Clone in a sandbox.** Run the agent in a disposable VM/container without host secrets. Check out the repo read-only until you are ready to stage a proposal branch.
3. **Study the rails.** Read `docs/workflow.md`, `_plans/README.md`, and `docs/AGENTS.md` to understand plan discipline, receipts, and OCERS framing.
4. **Capture a manifest.** Copy `AGENT_MANIFEST.example.json` to `AGENT_MANIFEST.json`, fill in the metadata (agent id, human owner, capabilities, limits).
5. **Scout micro-tasks.** Run local discovery (tests, lint, queue prompts). Stay within ~30 LOC and target high-leverage fixes (docs, tests, small bugs).
6. **Propose before editing.** For each task (max 3 per session):
   - Duplicate `_plans/1970-01-01-agent-template.plan.json` → `_plans/<ISOdate>-<slug>.plan.json`.
   - Fill in `actor`, `steps`, and `checkpoint`.
   - Add a matching justification Markdown file (see template) with evidence and receipts.
7. **Announce your session.** Run `python -m tools.agent.session_boot --agent <agent-id>` to log a handshake event and see other active agents.
8. **Claim the task on the bus.** `python -m tools.agent.bus_claim claim --task <id> --plan <plan_id>` records ownership in `_bus/claims/` (one active claim per task).
9. **Commit to an agent branch.** Use `git checkout -b agent/<agent-id>/<slug>` (or run `tools/agent/runner.sh` which scaffolds the branch and test loop).
10. **Log progress events.** Append milestones with `python -m tools.agent.bus_event log --event proposal --task <id> --summary "..."` so peers and auditors can track status.
11. **Open a draft PR.** Include the plan + justification, update receipts, and attach the OCERS evidence in PR body. Label with `bot:autocollab`.
12. **Release the claim after merge.** `python -m tools.agent.bus_claim release --task <id> --status done` and log a final event.
13. **Handshake refresh if staying on.** Re-run `python -m tools.agent.session_boot --agent <agent-id> --summary "session wrap"` when you finish or plan to idle, so the bus reflects your state.
14. **Wait for human review.** CI will validate plans and enforce agent safeties; humans gate merges. Keep tokens revocable and rotate after sessions.

## Safety Defaults

- Plans + justifications are mandatory for any `agent/*` branch PR (enforced in CI).
- Rate-limit yourself to 3 proposals per 24h unless trusted maintainers expand the budget.
- Sandbox execution; do not access personal data or external secrets.
- Revoke credentials when finished and append a memory entry so the revocation is auditable. Store the receipt at `_report/agent/<agent-id>/revoke-<timestamp>.json` and reference it: `python tools/memory/log-entry.py --summary "Revoked <token> for <agent-id>" --ref agent/<id>/revoke-<date> --artifact _report/agent/<agent-id>/revoke-<timestamp>.json`.

## Files to Know

- `AGENT_MANIFEST.example.json` → copy to describe your agent.
- `_plans/1970-01-01-agent-template.plan.json` → JSON template for receipts-first planning.
- `_plans/agent-proposal-justification.md` → Markdown pattern for evidence.
- `tools/agent/runner.sh` → optional helper to stage branches, run tests, and push.
- `tools/agent/bus_claim.py`, `bus_event.py`, `bus_status.py`, `session_boot.py` → manage the coordination bus.
- `tools/agent/bus_watch.py` → tail or filter events (`python -m tools.agent.bus_watch --since <ts> --agent codex-2 --event status`).
- `_bus/README.md` → explains claims/events schemas and CI guardrails.

Questions? Open a discussion or ping maintainers before expanding scope. Receipts and human checkpoints keep the network safe.
