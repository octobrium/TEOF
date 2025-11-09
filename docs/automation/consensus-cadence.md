# Consensus Cadence Guard

Defines the recurring review rhythm for consensus decisions (QUEUE-032) plus the receipts and guardrails required before automation proceeds.

## Cadence overview

| Frequency | Actor | Commands | Receipts |
| --- | --- | --- | --- |
| Daily (async) | rotating engineer | `python -m tools.consensus.ledger --limit 5`<br>`python -m tools.consensus.dashboard --format table --since 24h` | `_report/agent/<id>/consensus/daily-<ISO>.md` |
| Weekly (manager) | active manager | `python -m tools.consensus.receipts --decision WEEKLY-<ISO>`<br>`python -m tools.consensus.dashboard --format table --since 7d --markdown _report/manager/consensus-weekly-<ISO>.md` | `_report/manager/consensus-weekly-<ISO>.md` + bus summary |
| Escalation | engineer on duty | `python -m teof bus_message log --task CONSENSUS-ESC --summary "<decision>" --severity high` | `_report/agent/<id>/consensus/escalations-<ISO>.json` |

Daily sweeps ensure each open consensus decision has receipts and a status. Weekly reviews summarize outcomes, link to manager reports, and capture escalations.

## Required commands

```bash
# Daily sweep (run once per timezone)
python -m tools.consensus.ledger --limit 5 \
  --out _report/agent/${AGENT}/consensus/daily-ledger-${DATE}.json
python -m tools.consensus.dashboard --format table --since 24h \
  > _report/agent/${AGENT}/consensus/daily-dashboard-${DATE}.txt

# Weekly manager packet
python -m tools.consensus.receipts \
  --decision WEEKLY-${ISO_WEEK} \
  --receipts-file _report/manager/consensus-weekly-${ISO_WEEK}.jsonl
```

Include the CLI outputs (JSON/markdown) in git so CI can confirm they exist.

## Guard rules

`QUEUE-032` requires:

1. `_report/agent/<id>/consensus/` contains at least one receipt from the last 48h.
2. `_report/manager/consensus-weekly-*.md` exists for the current ISO week.
3. `scripts/ci/check_consensus_receipts.py` passes (verifies summary + ledger receipts).
4. `docs/workflow.md` and `docs/parallel-codex.md` reference this cadence (already satisfied).

When any condition fails, Ethics flags `missing_guard_receipt` on QUEUE-032; add the missing receipts and rerun the guard.

## Evidence threading

- Daily receipts reference the bus summary or decisions touched.
- Weekly receipt includes:
  - `decisions_reviewed`: array of decision IDs linked to ledger entries.
  - `escalations`: actions taken for missing receipts.
  - `next_actions`: tasks for upcoming week.
- Manager reports link to the weekly markdown so reviewers can audit cadence compliance.

## Automation hooks

- `scripts/ci/check_consensus_receipts.py` runs on every CI job, failing if `latest.json` is stale or the summary file is missing.
- `scripts/ci/consensus_smoke.sh` executes in CI to keep the tooling healthy; add the most recent receipts to `_report/consensus/`.

Maintainers can extend the cadence (e.g., monthly aggregate) by updating this doc and adding the new receipt paths to the guard.
