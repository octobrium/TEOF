# Plan Justification — 2025-09-18-consensus-ci

## Why this helps
Consensus tooling (ledger CLI, receipts helper, dashboard) now exists but CI still ignores it. Integrating smoke checks into teof-ci ensures regressions fail early and receipts stay reproducible.

## Proposed change
1. Add a CI script that exercises the consensus CLIs end-to-end (generate sample ledger, run ledger/receipts/dashboard commands, capture receipts).
2. Update the main CI workflow to run the consensus smoke script and targeted pytest modules.
3. Store resulting artifacts for debugging via workflow upload.

## Receipts to capture
- `_plans/2025-09-18-consensus-ci.plan.json`
- `_report/agent/codex-4/queue-038/consensus-ci-notes.md`
- Consensus CI smoke output captured in `_report/agent/codex-4/queue-038/consensus-ci-smoke.log`

## Tests / verification
- `pytest tests/test_consensus_ledger_cli.py tests/test_consensus_receipts.py tests/test_consensus_dashboard.py`

## Ethics & safety notes
Automation only; no production impact beyond CI coverage.
