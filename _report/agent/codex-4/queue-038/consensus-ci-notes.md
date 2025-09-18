# QUEUE-038 — Consensus CI Integration
- Added scripts/ci/consensus_smoke.sh to exercise ledger/receipts/dashboard CLIs with sample data and store artifacts.
- teof-ci workflow now runs the smoke script, targeted pytest modules, and uploads consensus artifacts.
- pytest receipt: _report/agent/codex-4/queue-031/pytest-consensus-receipts.txt (previous) and new log _report/agent/codex-4/queue-038/consensus-ci-smoke.log.
