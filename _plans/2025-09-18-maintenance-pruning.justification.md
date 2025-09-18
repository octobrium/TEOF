# Agent Proposal Justification — 2025-09-18-maintenance-pruning

## Why this helps
The repo accumulates historical plans, receipts, and log artifacts quickly. Without a regular pruning cadence, agents pay an increasing observation tax before every session. A recurring maintenance sweep keeps `_plans/`, `_report/`, and bus logs lean.

## Proposed change
Establish a pruning workflow that inventories stale plans (status done > 48h), archives or removes obsolete receipts, and compacts bulky docs. Document the cadence and produce a receipt summarizing the trimmed artifacts.

## Receipts to collect
- `_report/agent/codex-3/maintenance-pruning/summary.json`

## Tests / verification
- `python3 tools/planner/validate.py`
- `pytest tools/tests/test_pruning.py` (if new helpers added) or **N/A** if no code change.

## Ethics & safety notes
Operations remain within the repo; ensure append-only governance files stay untouched.
