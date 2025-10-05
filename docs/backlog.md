# Backlog Source of Truth

TEOF treats the backlog as the canonical queue for every agent. Before writing
code or touching the bus, confirm your next move here.

## Layers to check
- **Next Development list** – `_plans/next-development.todo.json` is the ranked
  backlog managers maintain. Pick the first pending item that matches your seat
  once trust + CI requirements are satisfied.
- **Active plans** – `_plans/*.plan.json` capture the receipts, steps, and
  checkpoints for current work. If you adopt a plan, update its steps before
  making changes.
- **Live claims** – `_bus/claims/*.json` show who owns which queue entries. Claim
  your task with `python -m tools.agent.bus_claim claim --task <id> --plan
  <plan_id>` so other seats see you working.

## Daily rhythm
1. **Read the backlog** – start each session by scanning
   `_plans/next-development.todo.json` (or run `python -m tools.planner.cli list
   --pending` when automation lands).
2. **Claim deliberately** – only touch the bus after `session_boot`; then claim
   the task and point to the plan you will advance.
3. **Update receipts first** – plans, claims, and manager-report notes must stay
   in sync. If your plan changes, amend the backlog entry or add a new plan.
4. **Escalate gaps** – if you see missing steps, conflicting claims, or stale
   backlog entries, log it on manager-report and capture a receipt before
   proceeding.

## Entry points
- `python -m tools.agent.doc_links show backlog-source`
- `docs/onboarding/README.md` (First Hour Path, Daily Loop)
- `_plans/next-development.todo.json`
- `_bus/claims/`

Keeping these artifacts current is what allows short prompts like “proceed as
indicated” to make sense—everything else flows from the backlog.
