# Capsule Release Cadence

## Frequency
- Target cadence: review capsule readiness weekly; freeze/releases at least once per month or after major governance milestones.
- Trigger early if consensus dashboard flags pending capsule updates or governance anchors diverge.

## Required Steps (next target freeze: 2025-09-19T02:00Z)
1. Run `python -m tools.consensus.dashboard --task QUEUE-030 --task QUEUE-031 --since <ISO>` to confirm ledger and receipts are up to date.
2. Freeze hashes: `bash scripts/freeze.sh` (records `capsule/<version>/hashes.json`).
3. Update status markers: ensure `capsule/README.md` lists the active version and update/create `capsule/vX.Y/STATUS.md` (active vs archived).
4. Append governance anchor: update `governance/anchors.json` with `prev_content_hash` and capsule metadata.
5. Update docs: refresh `docs/workflow.md` release block if cadence or checklist changes.
6. Tag/release per `docs/workflow.md` (Lean release block).

## Roles & Receipts
- **Release engineer:** runs freeze + status updates, records receipts under `_report/agent/<id>/capsule-release/` (include freeze output and STATUS diff).
- **Manager:** verifies governance anchor entry and posts summary in `manager-report` (attach dashboard and release receipts).
- **Observer:** cross-checks capsule README/STATUS during consensus review.

## Escalation
- If release slips beyond cadence, escalate in `manager-report` and open QUEUE item to track blockers.
- Remediate missing receipts before declaring release complete (dashboard should show receipts attached).
