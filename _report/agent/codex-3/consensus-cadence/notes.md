# Consensus Cadence Notes — 2025-09-20

- Recap of documented loop:
  - Daily async sweep: agents run `python -m tools.consensus.dashboard` with QUEUE-030..033 to surface missing receipts and stale updates, escalating via `bus_message --type request` when gaps persist beyond 24h.
  - Weekly manager review: manager executes dashboard + ledger commands, records receipts under `_report/consensus/`, and posts summary in `manager-report` (see docs/parallel-codex.md and docs/workflow.md updates dated 2025-09-18).
- Dependency mapping:
  - Dashboard tooling lives in `tools/consensus/dashboard.py`; CI coverage wired via `scripts/ci/consensus_smoke.sh` and `pytest tests/test_consensus_dashboard.py`.
  - Release cadence aligns with `docs/maintenance/capsule-cadence.md` (capsule readiness checks now reference consensus receipts before freeze).
- Follow-through receipts:
  - Docs refreshed in `docs/parallel-codex.md` and `docs/workflow.md` to codify daily/weekly checkpoints and escalation path.
  - Validation guard: `python3 tools/planner/validate.py --strict` run 2025-09-20T09:15Z (receipt `_report/planner/validate/summary-20250920T091507Z.json`).
- Next watchpoint: ensure consensus dashboard receipt attachments appear in the next manager heartbeat sweep; open QUEUE follow-up if weekly summary lacks ledger attachment.
