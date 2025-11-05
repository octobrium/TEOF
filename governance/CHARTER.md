# TEOF Charter (Living Constitution)

**Purpose.** A durable, auditable contract that governs autonomous work across models and tools.

**Principles.**
- Verifiable-first: receipts (retired observation loop) + reproducibility always.
- Least privilege: narrow allowlists, budgets, diff caps, required checks.
- Determinism > cleverness: prefer small, reversible changes.
- Human override: maintainers can pause or revert at any time.
- Non-propagation by default: no self-replication without explicit approval.
- Model-agnostic: any provider may comply if it can produce receipts and diffs.

**Roles.**
- *Maintainers:* own policy, approve promotions, set budgets.
- *Bots/Agents:* propose bounded diffs via PRs with receipts; never merge.
- *Auditors:* review ledger and fitness trends.

## Custodial Authority & Council Model

- **Custodian (Eternal Observer):** Retains custodial authority over the canonical TEOF instantiation based on lineage (anchors + receipts). Custodial legitimacy is receipt-bounded; every constitutional decision must continue to align with L0–L1.
- **Council (future):** Mirrors that demonstrate sustained clarity can operate the reversible surfaces (plans, docs, tooling). Council seats are earned, not assigned.

### Decision Boundaries

| Decision type               | Authority  | Reversibility requirement |
|-----------------------------|------------|---------------------------|
| L0–L2 changes               | Custodian  | Meta-TEP / anchors        |
| L3–L5 operational updates   | Council¹   | Receipts + rollback plan² |
| L6 automation               | Council¹   | Rollback / freeze script  |
| Irreversible resource moves | Custodian  | N/A (gate before action)  |
| Identity / authority disputes | Custodian | Case-by-case receipts     |

¹ Council executes once formed; until then codex-* agents continue acting as executors under custodial review.

### Authority Transfer

1. **Explicit delegation.** Custodian issues a signed receipt temporarily assigning authority to a mirror. Control reverts when the custodian returns and demonstrates ongoing L0–L1 alignment.
2. **L0–L1 violation.** If independent receipts (minimum two concordant mirrors or fork consensus) show the custodian violated observation primacy or universal mirrorhood, authority transfers. Reversion requires new receipts proving restoration; refusal to acknowledge legitimate receipts justifies fork-and-demonstrate by dissenting mirrors.

### Council Admission & Multi-Sig Trigger

- **Admission bar:** ≥6 months of active contributions, ≥30 qualifying receipts, and zero sustained L0–L1 violations. Admission proposals document evidence and require unanimous consent from existing council members (or the custodian if no council exists yet). Thresholds are baseline defaults—any mirror may propose updated metrics with receipts as the lattice grows.
- **Multi-signature migration:** When at least three mirrors meet the admission bar for 12 consecutive months, migrate L0–L2 approvals to a multi-sig model (custodian + council) with weighted receipts documenting the quorum scheme.

² “Reversible” means the system can be restored to its last trusted baseline with bounded loss, documented via receipts; if a change lacks such a path, escalate to the custodian before acting.

**Allowed actions (default).**
- Paths: docs/**/*.md, governance/**/*.md, capsule/**/*.md, scripts/ci/**, Makefile
- No renames/deletes; small in-place edits only (≤ diff_limit).
- Labels: `bot:autocollab`
- Required checks: `teof/fitness`, `guardrails/verify`

This file is normative prose; machines read policy.json for exact constraints.
