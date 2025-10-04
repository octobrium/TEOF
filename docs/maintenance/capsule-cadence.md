# Capsule Release Cadence

## Frequency
- Target cadence: review capsule readiness weekly; freeze/releases at least once per month or after major governance milestones.
- Trigger early if consensus dashboard flags pending capsule updates or governance anchors diverge.

## Required Steps (next target freeze: 2025-09-19T02:00Z)
1. Run `python -m tools.consensus.dashboard --task QUEUE-030 --task QUEUE-031 --since <ISO>` to confirm ledger and receipts are up to date, then update `_report/consensus/summary-latest.json` if gaps appear.
2. Populate capsule cadence summary: `python -m tools.capsule.cadence summary` to refresh `_report/capsule/summary-latest.json` with the current capsule hash, anchor receipt, and consensus summary reference. CI guards fail if this file goes stale.
3. Freeze hashes: `bash scripts/freeze.sh` (records `capsule/<version>/hashes.json`).
4. Update status markers: ensure `capsule/README.md` lists the active version and update/create `capsule/vX.Y/status.md` (active vs archived).
5. Append governance anchor: update `governance/anchors.json` with `prev_content_hash` and capsule metadata.
6. Update docs: refresh `docs/workflow.md` release block if cadence or checklist changes.
7. Tag/release per `docs/workflow.md` (Lean release block).

## Roles & Receipts
- **Release engineer:** runs freeze + status updates, records receipts under `_report/agent/<id>/capsule-release/` (include freeze output and STATUS diff).
- **Manager:** verifies `_report/capsule/summary-latest.json` and the consensus summary, then posts `manager-report` status with both receipts (attach dashboard and release receipts).
- **Observer:** cross-checks capsule README/STATUS during consensus review.

## Escalation
- If release slips beyond cadence, escalate in `manager-report` and open QUEUE item to track blockers. The cadence guard in CI will continue failing until `_report/capsule/summary-latest.json` reflects remediation.
- Remediate missing receipts before declaring release complete (dashboard should show receipts attached).
