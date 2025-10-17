# Ideas Index

Use this checklist to shepherd an idea from observation to a backlogged plan.

1. **Observation** — Capture the raw signal (reflection, scan receipt, bus note).
2. **Idea draft** — `teof ideas mark <slug> --status draft --layer L? --systemic ?`. Keep the note short; link to the observation receipt.
3. **Triage** — Update status to `triage` and record the intended steward. Consider adding `--notes` via `teof ideas mark`.
4. **Readiness scan** — Run the relevant guard (`teof scan --only critic` etc.) to confirm no precursor work is missing.
5. **Promotion decision** — If the idea still holds, open a plan (`python -m tools.planner.cli new ...`) and then `teof ideas promote <slug> --plan-id <plan>`.
6. **Backlog link** — If a task queue entry exists, create/refresh the bus claim (`python -m tools.agent.bus_claim claim ...`).
7. **Execution** — Work proceeds in the plan; update the idea with status `in_progress` only if major research continues outside the plan. Otherwise leave it `promoted`.
8. **Closure** — When the plan finishes, either archive (`teof ideas mark --status archived`) or append receipts explaining why the idea remains open for future extensions.

This path keeps retired observation loop coordinates attached from the moment an idea surfaces, and ensures every promoted concept has receipts tying it to plans, claims, and downstream automation.
