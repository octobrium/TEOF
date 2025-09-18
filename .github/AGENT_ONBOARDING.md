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
10. **Managers assign tasks.** Use `python -m tools.agent.task_assign --task <id> --engineer <agent>` to record assignments (writes `_bus/assignments/<task>.json` and appends `_bus/messages/<task>.jsonl`). Engineers should acknowledge with a `bus_event` status message.
11. **Log progress events.** Append milestones with `python -m tools.agent.bus_event log --event proposal --task <id> --summary "..."`; managers can monitor via `python -m tools.agent.bus_watch --limit 20 --follow` and run `python -m tools.receipts.main check` to validate receipts.
12. **Open a draft PR.** Include the plan + justification, update receipts, and attach the OCERS evidence in PR body. Label with `bot:autocollab`.
13. **Generate manager summary.** When a bundle of work is ready, run `python -m tools.agent.manager_report` to emit `_report/manager/manager-report-<timestamp>.md` summarising consensus and linking receipts.
14. **Release the claim after merge.** `python -m tools.agent.bus_claim release --task <id> --status done` and log a final event; managers can post a `consensus` message via `bus_event log --event consensus ...` to signal readiness.
15. **Handshake refresh if staying on.** Re-run `python -m tools.agent.session_boot --agent <agent-id> --summary "session wrap"` when you finish or plan to idle, so the bus reflects your state.
16. **Wait for human review.** CI will validate plans and enforce agent safeties; humans gate merges. Keep tokens revocable and rotate after sessions.

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
- `tools/agent/bus_claim.py`, `bus_event.py`, `bus_status.py`, `session_boot.py` → manage the coordination bus (use `bus_status --agent <id> --active-only --json` to script dashboards).
- `tools/agent/task_assign.py`, `manager_report.py` → manager utilities for assigning work and producing summaries.
- `tools/receipts/main.py check` → quick validation that plan receipts exist locally before opening a PR.
- `tools/agent/bus_watch.py` → tail or filter events (`python -m tools.agent.bus_watch --since <ts> --agent codex-2 --event status`).
- `_bus/README.md` → explains claims/events schemas and CI guardrails.

Questions? Open a discussion or ping maintainers before expanding scope. Receipts and human checkpoints keep the network safe.
