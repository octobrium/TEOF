---
title: Decentralized propagation pilot (cross-node receipts)
batch: 20250922T190055Z
item: 01
systemic_targets: ["S3", "S4", "S6"]
layer_targets: ["L3", "L4", "L5"]
risk_score: 0.3
generated: 20250922T190055Z
note: Draft pilot plan to validate TEOF as a permissionless receipt network before codifying new properties.
---

# Proposal
## Task: Pilot cross-node receipt exchange and reconciliation

### Problem / Motivation
We now articulate decentralized propagation principles in `docs/specs/connectivity.md`, but we lack evidence that multiple independent TEOF nodes can:
- produce signed receipts offline,
- exchange and aggregate those receipts without central coordination, and
- reconcile divergent states while preserving anchors and plan provenance.
Without a pilot, promoting decentralized traits into canonical properties would be premature and potentially risky.

### Proposed Pilot
1. **Scope Definition (S1)**
   - Participants: at least three independent nodes (e.g., steward laptops or sandboxes) running the published capsule.
   - Receipts exchanged: `_report/usage/external-summary.json`, `_report/usage/receipts-hygiene-summary.json`, and plan receipts tied to a shared task id.
   - Success criteria:
     - Each node reproduces the canonical quickstart (`teof brief`) and logs receipts locally.
     - Nodes publish hashes + metadata via `tools.agent.session_brief --preset operator` (or equivalent) to a shared exchange directory.
     - An aggregator script verifies signatures/hashes, merges receipts, and highlights conflicts.
     - Reconciliation rules documented (e.g., most recent anchor wins, conflicting hashes trigger human review).

2. **Prototype Exchange (S2)**
   - Deliver `tools/network/receipt_sync.py` (working name) that:
     - accepts multiple node directories,
     - verifies receipt hashes and timestamps,
     - emits a consolidated ledger under `_report/network/` with lineage per node,
     - writes a JSON diff for conflicts (hash mismatch, missing anchors, stale data).
   - Include an integration test with synthetic node directories to prove deterministic merging.

3. **Evaluation & Risk Review (S3)**
   - Document reconciliation results in `_report/network/<UTC>/summary.json` plus human-readable markdown.
   - Categorise risks (Byzantine node, replay attacks, receipt withholding) and list required mitigations before decentralisation becomes canonical.
   - Recommend go/no-go for promoting decentralized propagation into L3 properties based on pilot evidence.

### Acceptance Criteria
- Plan `2025-09-22-decentralized-propagation-pilot` is marked done with receipts for each step (scope doc, prototype run, evaluation report).
- Aggregator script + tests land under `tools/network/` (or another architecture-approved location) without introducing external dependencies beyond stdlib/PyNaCl.
- `_report/network/latest` contains the consolidated ledger and conflict report from a dry-run using synthetic node inputs.
- Risks + mitigations captured in `docs/proposals/…` or `_report/network/summary.md` for future governance consideration.

### Systemic Rationale
- **S3 Propagation** — multiplies verifiable receipts and exposes network state.
- **S4 Resilience** — ensures independent nodes resolve to a shared truth.
- **S6 Truth / L4 Architecture** — reconciliation logs highlight drift and trigger fixes while informing governance promotion.

### Sunset / Fallback
- If the pilot fails to reconcile nodes deterministically, document blockers and keep decentralized propagation in `docs/specs/` only. Revisit after tooling or governance updates address identified gaps.

---

## Status
Draft — awaiting steward assignment and pilot execution.

## Synthetic Evaluation & Risk Notes (S3 draft)
- The `tools/network/receipt_sync.py` prototype merges receipts from multiple nodes and flags conflicts via `conflicts.json` and `summary.md`. Synthetic tests (`tests/test_receipt_sync.py`) demonstrate detection when nodes produce divergent `_report/usage/external-summary.json` payloads.
- Conflict handling currently halts at reporting; escalation policy should require human review (link to plan step) and optionally bus alerts before promotion to canonical property.
- Identified risks:
  - **Byzantine node** — malicious nodes could submit forged receipts; mitigation requires signature verification (future work: integrate with authenticity envelopes).
  - **Receipt withholding** — nodes may omit critical `_report` files; aggregator should compute coverage ratios and warn on missing expected artifacts.
  - **Stale anchors** — reconciliation must respect governance anchors; pilot should include hash verification against `capsule/*/hashes.json`.
- Recommendation: run the pilot with at least one intentionally divergent node to exercise conflict reporting before proposing L3 promotion.
