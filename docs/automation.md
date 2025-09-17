# L6 Automation (Working Notes)

**Purpose:** describe how automated actors (bots, scripts, agents) operate inside TEOF while serving L0–L5.

## Core Duties

1. **Obey upper layers.** Automation inherits obligations from Observation (L0) through Workflow (L5); it may not bypass safeties or append-only rules.
2. **Emit receipts.** Every automated action must generate auditable receipts (`_report/…`) and, when appropriate, link to plans or memory entries.
3. **Expose capabilities.** Bots publish what they can do (e.g., `autocollab`, `ledger`) via hello packets or README snippets so peers know when to trust them.
4. **Stay reversible.** Prefer actions that can be rolled back or replayed from receipts; if irreversibility is unavoidable, require human checkpointing.
5. **Request consent signals.** When touching shared governance (anchors, capsules), automation should wait for maintainers or policy scripts to confirm.

## Operational Modes

- **Fast lane:** low-risk tasks (e.g., queue hygiene, ledger append) with auto receipts and immediate logging.
- **Guarded lane:** higher-risk operations require an open plan step and manual approval before execution.
- **Dissent lane:** if automation detects conflicts (hash mismatches, policy failures), it pauses, emits a warning, and prompts human review.

## Interfaces

- **Hello packet:** `tools/reconcile_hello.py` – publish hashes + capabilities.
- **Diff + Fetch:** `tools/reconcile_diff.py`, `tools/reconcile_fetch.py` – reconcile across instances.
- **Plans:** automation should claim steps via `tools/planner.cli step set …` so provenance is consistent.

## Open Questions

- Should automation maintain its own ledger of actions separate from `_report/`? (Potential future work.)
- How to encode confidence/calibration for automated decisions?
- When multiple bots disagree, who arbitrates? (Candidate: anchors events with human signatures.)

Automation extends workflow without creating a new authority: it accelerates mundane actions, but humans and higher layers remain the governors of meaning and safeties.
