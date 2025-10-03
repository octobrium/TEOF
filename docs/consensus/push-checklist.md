# Consensus Push Checklist (Receipts-Proven)

Use this checklist whenever you prepare to push `main` after multi-agent consensus. Each step must leave a receipt so the push remains auditable.

## 1. Consensus Evidence
- [ ] Latest `manager-report` (via `python -m tools.agent.manager_report --log-heartbeat`) is stored under `_report/manager/` and notes the consensus decision.
- [ ] Bus events in `manager-report` channel show approvals from the required agents with receipts (claim IDs, tests, etc.).
- [ ] Session reflections covering the decision are logged under `memory/reflections/`.

## 2. Plan & Receipt Hygiene
- [ ] Run `python3 tools/agent/manager_report.py` and ensure *Plan Validation Issues* is empty (fix failing `_plans/*.plan.json` before proceeding).
- [ ] For touched plans, run `python -m tools.planner.validate --strict <plan>`; update receipts referenced in plans if necessary.
- [ ] Clear any lingering `git update-index --assume-unchanged` flags (`python -m tools.agent.reset_assume_unchanged clear`) and note the action on the bus.

## 3. Test Receipts
- [ ] Execute the relevant `pytest` suites (or full `pytest` when feasible).
- [ ] Capture test receipts/logs under `_report/` (for example, `_report/runner/` or case-study summaries) and stage them.

## 4. Final Bus Update
- [ ] Log `python -m tools.agent.bus_event log --event status --task manager-report --summary "consensus push ready" --receipt <manager-report>` so other agents can verify the state.

## 5. Push & Confirm
- [ ] `git status -sb` shows only intentional changes; no dirty handoffs remain.
- [ ] Run `git push origin main`.
- [ ] Post-push, drop a short bus message with the commit hash and key receipts.

Keep the completed checklist alongside the manager report for future audits.
