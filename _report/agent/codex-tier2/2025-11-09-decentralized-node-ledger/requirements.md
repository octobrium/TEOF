# ND-069 Ledger Requirements (2025-11-09T05:12Z)

Sources reviewed:
- `queue/069-node-incentive-ledger.md`
- `_plans/2025-10-11-decentralized-node.plan.json`
- `docs/ideas/decentralized-teof-node.md`
- `docs/automation/decentralized-propagation.md`
- Latest scan receipts `_report/agent/codex-tier2/teof-scan-20251109B/frontier.json` + `critic.json`

Key requirements:
1. **Ledger Scope** – Track stake, reputation, and governance approvals for every decentralized node seat. Entries must cite: node id, action (join, reward, penalty), receipts proving work, issuing authority, and resulting reputation delta. (Queue brief + ideas doc.)
2. **Schema & Storage** – Append-only JSONL under `_report/usage/node-incentive-ledger/` plus machine schema in `schemas/node-incentive-ledger.schema.json`. Needs hash chaining or anchor reference to `governance/anchors.json` for audit.
3. **CLI / Automation** – New helper (e.g., `python -m tools.autonomy.node_ledger`) to append and inspect entries; integrates with `teof foreman`/scan so critic can confirm ledger receipts exist. Hooks must enforce that any node-granting plan references a ledger entry.
4. **Governance Workflow** – Define approval steps: proposal (plan), verification (receipts), ratification (anchors), and distribution (ledger entry). Must align with CMD-1/5/7 and escalate uncertainty via manager-report.
5. **Receipts** – Each ledger action emits `_report/usage/node-incentive-ledger/<timestamp>.json` plus referenced proofs (plan receipts, bus events). Automation needs regression tests verifying schema + CLI behavior.

Open questions:
- How do we bootstrap initial reputation? (Probably via existing codex seats + retroactive receipts.)
- Do we require multi-sig approvals or quorum? Need to define in governance doc.

Next steps: promote these notes into plan S1 completion, then draft schema in S2.
