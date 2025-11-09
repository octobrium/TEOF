<!-- markdownlint-disable MD013 -->
# Decentralized Node Governance Binder

Status: Living  
Linked plan: `2025-10-11-decentralized-node` (ND-073)  
Receipts: `_report/usage/plan-scope/plan-scope-2025-10-11-decentralized-node-20251109T232218Z.json`, `_report/usage/hash-ledger/receipt-20251109T231337Z.json`

## Purpose

Give remote TEOF nodes a deterministic governance playbook—claims, receipts, incentives, and escalation—so any operator can join/exit without bespoke coordination. This document *is* the binder referenced in `queue/073-decentralized-node-governance.md`.

## Activation Workflow (follow in order)

1. **Retrieve the plan scope receipt**
   ```bash
   python3 -m teof plan_scope --plan 2025-10-11-decentralized-node
   ```
   Store the emitted `_report/usage/plan-scope/...json` alongside your node receipts.

2. **Seat the manifest + claim**
   ```bash
   python3 -m tools.agent.manifest_helper activate <node-id>
   python3 -m teof bus_claim claim --task ND-073 --plan 2025-10-11-decentralized-node --branch agent/<node-id>/nd-073
   ```
   Log your presence on `manager-report` via `python3 -m teof bus_message --task manager-report --type status ...`.

3. **Apply ant-colony stewardship**
   ```bash
   python3 -m tools.agent.stale_claims --agent <node-id> --threshold-hours 6 --fail-on-stale
   ```
   Release (`--release`) before stepping away so the next operator can continue without delay.

4. **Anchor receipts**
   - After generating plan-scope or guard receipts, append them to the hash ledger:
     ```bash
     python3 -m teof hash_ledger append \
       --plan 2025-10-11-decentralized-node \
       --step S3 \
       --receipt _report/usage/plan-scope/<file>.json \
       --agent <node-id> \
       --ts $(date -u +%Y-%m-%dT%H:%M:%SZ) \
       --metadata <path-to-metadata.json>
     ```
   - Guard integrity with `python3 -m teof hash_ledger guard` (CI enforces this via `scripts/ci/check_hash_ledger.py`).

5. **Deliver governance artifacts**
   - This binder (`docs/usage/autonomous-node-governance.md`) + workflow receipts
   - Incentive summaries (`docs/usage/autonomous-node/…/summary.json`)
   - Any manager-report tails required by the hosting org

## Incentives & Ledger

* Goal: reward nodes that maintain receipts-first coordination.
* Trace contributions via the hash ledger; payout scripts only consider entries with valid hashes, anchored plan IDs, and manager-report references.
* Minimum bundle for payout review:
  1. Handshake receipt (`_report/agent/<node-id>/session_boot/...json`)
  2. Plan-scope receipt
  3. Hash-ledger entry (`_report/usage/hash-ledger/receipt-*.json`)
  4. Summary reflection (preferred: `memory/reflections/...json`)

## Claim & Escalation Guardrails

| Requirement | Command |
| --- | --- |
| Release idle claims | `python3 -m tools.agent.stale_claims --agent <node-id> --threshold-hours 6 --release` |
| Escalate blockers | `python3 -m teof bus_message --task manager-report --type status --summary "escalation" --meta severity=high` |
| Ethics handoff | `python3 -m teof bus_event log --event status --severity high --task ETHICS-ND-068 --summary "<why>"` |
| Receipt mirror | `python3 -m teof hash_ledger guard` (CI) |

## Receipt Bundle Checklist (per node)

- [ ] `_report/agent/<id>/session_boot/coordination-dashboard-*.json`
- [ ] `_report/usage/plan-scope/plan-scope-2025-10-11-decentralized-node-*.json`
- [ ] `_report/usage/hash-ledger/receipt-*.json`
- [ ] `_report/usage/hash-ledger/metadata-*.json`
- [ ] `docs/usage/autonomous-node-governance.md` (this file)
- [ ] Reflection referencing the run (`memory/reflections/...json`)

## Updates

| Date (UTC) | Change | Receipt |
| --- | --- | --- |
| 2025-11-09 | Ant-colony pickup: binder authored, hash-ledger anchor recorded | `_report/usage/hash-ledger/receipt-20251109T231337Z.json` |

Treat this binder as the living contract for decentralized nodes. Improve it via the plan (`2025-10-11-decentralized-node`) and append new receipts when governance evolves.
