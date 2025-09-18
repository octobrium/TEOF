# Plan Justification — 2025-09-18-consensus-ledger-cli

## Problem
Consensus work requires a deterministic view of ledger-backed decisions. Right now, agents must inspect `_report/ledger.csv` or rerun `tools/ledger.sh` manually, which provides console output but no filterable CLI for consensus checkpoints. Queue item `030-consensus-ledger-cli` asks for a first-class interface so consensus automation can introspect votes, risk, and receipts.

## Proposal
Implement `python -m tools.consensus.ledger` as a read-only CLI that:
- Loads `_report/ledger.csv` (and future consensus artifacts) and emits filtered summaries by decision id, agent, and timeframe.
- Supports `--format table|jsonl` so humans and automation can consume the same output.
- Integrates with existing ledger update scripts (`tools/ledger.sh`, `tools/pulse.sh`) without duplicating logic.
- Logs receipts under `_report/consensus/` whenever the CLI runs in CI or as part of consensus checks.

## Rationale
- **Observation:** Managers need a fast way to inspect ledger state when preparing consensus reviews.
- **Coherence:** Aligns with the consensus backlog themes and ties into the newly documented follow-up logging habit.
- **Reproducibility:** A dedicated CLI enables regression tests and recorded receipts rather than ad-hoc shell scripts.

## Receipts & Stakeholders
- Engineers will deliver new modules under `tools/consensus/` plus tests in `tests/test_consensus_ledger_cli.py`.
- Manager ownership tracked via `_plans/2025-09-18-consensus-ledger-cli.plan.json` and bus logs.

## Risks / Mitigations
- **Data drift:** Validate CSV headers before processing; fail fast with actionable errors.
- **Timeline:** Ensure the CLI ships read-only first; ledger mutations remain with existing automation to avoid accidental corruption.

## Next Steps
1. Approve plan below.
2. Engineer claims QUEUE-030 and implements CLI + tests.
3. Manager logs consensus receipts once CLI integrated into workflows.
