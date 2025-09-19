# 2025-09-21-code-compaction — Justification

## Objective
Shrink the OCERS/tooling footprint by eliminating duplicate logic and dead code while preserving deterministic behaviour.

## Success Criteria
- Inventory of compaction candidates committed (shared heuristics, redundant scripts, oversized docs).
- Code removals/refactors landed with receipts + regression tests proving unchanged outcomes.
- LOC/duplication delta recorded in receipts for manager review.

## Risks / Mitigations
- Behavioural drift: require existing tests + new targeted coverage before removing logic.
- Hidden dependencies: run imports/static analysis before deletion; stage changes behind feature flags if needed.
