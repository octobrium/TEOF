# Coordination Role Tension — 2025-11-09

**Context.** During ND-067 consolidation work, the non-technical coordinator indicated they would merge to `main` via the GitHub UI without reviewing diffs or receipts, delegating all technical assurance to automation agents.

**Tension.**
- **Expectation mismatch:** Coordinator intends to push directly while declining to review technical risk, but TEOF still holds agents accountable for the state of `_bus`, `_report`, and dirty artifacts. Without explicit cleanup, accidental receipts could hit `main`.
- **Guardrail coverage:** Operators assume “use TEOF” implies automation already ran required guardrails/tests. If the coordinator skips verification, agents must proactively document which receipts/commands ran before any merge request.
- **Authority vs. responsibility:** Granting “authority to guide” does not include push credentials for the agent, yet the coordinator expects end-to-end ownership. This gap surfaced when the agent could not push to `main` but remained responsible for merge quality.

**Mitigation.**
1. Record outstanding dirty files before approving a merge so coordinators see exactly what will land.
2. When automation cannot perform an action (e.g., `git push`), immediately log that limitation with a receipt and propose a guarded alternative (prepare branch, run guardrails, provide staging checklist).
3. Keep a standing “merge readiness” checklist (tests executed, guard receipts, staged files) in the plan notes so non-technical coordinators can reference a single artifact instead of reviewing diffs manually.

This note documents the coordination tension so future sessions can pre-negotiate merge responsibilities before automation cycles begin.
