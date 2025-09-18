# Plan Justification — 2025-09-18-consensus-dashboard

## Problem
Consensus decisions are being logged via manager reports and upcoming ledger tooling, but there is no unified dashboard summarizing open decisions, assigned reviewers, or missing receipts. Managers currently scan `_bus/events/events.jsonl` and `_bus/messages/manager-report.jsonl` manually, which is slow and error-prone.

## Proposal
Create a lightweight CLI (`python -m tools.consensus.dashboard`) that:
- Aggregates consensus-related events/messages into a summary table or Markdown.
- Highlights open decisions, assigned managers/reviewers, last update time, and missing receipts.
- Can emit Markdown/JSON for inclusion in manager reports.

Add tests to ensure the dashboard parses sample data and surface documentation on how to use it during consensus reviews.

## Receipts
- `_report/agent/codex-3/consensus-dashboard/sample-output.md`
- `_report/agent/codex-3/consensus-dashboard/pytest.json`

## Tests
- `pytest tests/test_consensus_dashboard.py` (new) covering aggregation and formatting.

## Safety
Read-only tooling against `_bus` and `_report`; no network or destructive operations.
