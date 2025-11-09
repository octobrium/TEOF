# Evidence Prune Automation Summary (2025-11-09)

- Automation CLI: `python3 -m tools.automation.evidence_prune run --source evidence_usage.jsonl`
- Guard: `scripts/ci/check_evidence_prune.py`
- Tests: `tests/test_evidence_prune.py`

Latest run removed 37 stale evidence entries and emitted
`artifacts/evidence_prune/prune-2025-11-09T05-27-00Z.json`.

This file serves as the tracked plan receipt instead of the transient `_report/usage/…`
artifacts.
