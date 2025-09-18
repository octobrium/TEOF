# Plan Justification — 2025-09-18-consensus-receipts

## Problem
Consensus decisions currently rely on ad-hoc receipts, making it difficult to guarantee that closing a decision emits the necessary evidence under `_report/consensus/`. Queue item `031-consensus-receipts.md` requests automation so receipts are appended consistently and linked to bus events.

## Proposal
Implement helper logic (likely in `tools/consensus/receipts.py` plus CLI integration) that:
- Accepts decision identifiers and receipt payloads, writing normalized JSONL entries into `_report/consensus/`.
- Integrates with `tools.agent.bus_event` (optional flag) so closing consensus decisions attaches the new receipt automatically.
- Provides pytest coverage to ensure receipt files are created and linked, and updates docs describing the workflow.

## Receipts & References
- `_plans/2025-09-18-consensus-receipts.plan.json` describing execution steps.
- Tests under `tests/test_consensus_receipts.py` to validate behavior.

## Risks / Mitigations
- Avoid overwriting existing receipts: append-only design with timestamped filenames.
- Ensure compatibility with the new ledger CLI by reusing schema components where possible.

## Next Steps
1. Approve the accompanying plan.
2. Implement append helper + bus integration.
3. Update consensus documentation with usage instructions.
