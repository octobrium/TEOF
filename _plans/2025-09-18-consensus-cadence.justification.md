# Plan Justification — 2025-09-18-consensus-cadence

## Why this matters
Consensus backlog work (QUEUE-030..033) introduces ledger tooling, receipt automation, and dashboards. Without a documented cadence, managers and engineers revert to ad-hoc reviews, undermining coherence and reproducibility. The external audit also highlighted governance drift when coordination rituals are implicit.

## Proposal
Document a recurring consensus review loop covering:
- Frequency and trigger conditions (e.g., every 24h or when backlog crosses thresholds).
- Roles (manager, reviewers, observers) and required receipts.
- Escalation path when consensus is blocked.

Update `docs/parallel-codex.md` (session loop) and `docs/workflow.md` (manager ladder) so agents know how to initiate and record consensus reviews. Add a short reference in `docs/agents.md` if needed.

## Deliverables
- Updated docs with cadence section and escalation guidance.
- Receipt summarising decisions (notes + references) under `_report/agent/codex-3/consensus-cadence/`.

## Tests / verification
- Documentation check via existing markdown lint (implicitly in CI).
- Manual verification: run `python -m tools.agent.bus_status` to confirm consensus backlog references align with new text.

## Safety
Documentation-only change; no automation or destructive operations. Ensures future automation has clear expectations.
