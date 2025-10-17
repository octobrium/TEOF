<!-- markdownlint-disable MD013 -->
# Systemic Adoption Guide

**Status:** Draft  
**Purpose:** Help external teams adopt TEOF’s systemic lattice (S/L coordinates) without migrating wholesale into this repository.

---

## 1. Who this guide is for

Teams that want the benefits of TEOF’s auditability—deterministic receipts, layered governance, systemic targets—but cannot or should not mirror the entire repo structure.

You may have:
- An existing engineering stack (monorepos, microservices, data lakes).
- Regulatory or compliance frameworks already in place.
- Multiple programming languages with heterogeneous tooling.

This guide provides a neutral path to integrate the systemic lattice while staying compatible with your current environment.

---

## 2. Adoption phases

| Phase | Goal | Outputs | Suggested artifacts |
|-------|------|---------|---------------------|
| **Phase 0: Orientation** | Understand TEOF axioms and systemic lattice. | Alignment charter, stakeholders. | Present sections 2–3 of this guide, whitepaper overview, `docs/foundation/systemic-scale.md`. |
| **Phase 1: Metadata & receipts** | Emit systemic_targets/layer_targets and deterministic receipts from existing workflows. | Receipt schema, signing keys, receipt storage. | Section 3 (metadata schema), Section 4 (receipts). |
| **Phase 2: Governance overlay** | Map current ethics/compliance models to systemic axes and layers. | Mapping matrix, policy diff notes, escalation playbooks. | Section 5 (governance mapping). |
| **Phase 3: Automation guardrails** | Align automation with layered obligations. | Guardrail scripts, CI hooks, dashboards. | Section 6 (automation hooks). |
| **Phase 4: Anchoring & convergence** | Append-only lineage and cross-node reconciliation. | Anchors event log, reconciliation receipts, cross-org contracts. | Section 7 (lineage & multi-node). |

---

## 3. Minimal schema & metadata

All artifacts should emit:

```jsonc
{
  "systemic_targets": ["S1", "S4", "S6"],
  "layer_targets": ["L4", "L5"],
  "systemic_scale": 6,
  "layer": "L5",
  "summary": "Guardrail deployment for ledger API",
  "receipts": [
    "s3://org-audit/ledger/2025-10-17/systemic_out/brief.json"
  ]
}
```

**Recommendations**
- Treat `systemic_targets` as sorted, unique tokens. Include the highest axis required to deploy safely.  
- Keep `layer` as the primary operational layer; `layer_targets` list supporting layers in order of influence.  
- Version your schema (`schema_version: 1`) so clients can evolve without breaking older receipts.

**Export options**
- YAML/JSON sidecars co-located with plan documents.
- Embedded metadata blocks in pull requests (e.g., GitHub check summaries).
- API responses for downstream audit systems.

See `tools/planner/systemic_targets.py` for canonical parsing logic that you can port to other languages.  
Refer to `docs/automation/systemic-schema.md` for a field-by-field explanation and validation workflow.

---

## 4. Receipts & provenance

1. **Detached receipts:** Store outputs (`brief.json`, `score.txt`, dashboards) under a tamper-evident location (object storage, append-only log) with SHA-256 hashes.  
2. **Signature envelope:** Adopt the external adapter format (`teof-external-adapter` reference) to sign receipts with Ed25519 keys registered in append-only anchors.  
3. **Indexing:** Mirror TEOF’s `receipts_index` concept—a periodic job that enumerates receipts, flags missing entries, and publishes metrics.  
4. **Latency monitoring:** Track deltas between observation (ticket creation) and receipts landing. Align thresholds with your risk model.

You can start with a simple JSON envelope:

```json
{
  "artifact": "gs://team-a/systemic_out/20251017T031500Z/brief.json",
  "hash_sha256": "...",
  "systemic_targets": ["S6", "S4"],
  "layer_targets": ["L4"],
  "issued_at": "2025-10-17T03:15:12Z",
  "signature": "<base64url-ed25519>",
  "public_key_id": "team-a-signed"
}
```

---

## 5. Mapping existing governance models

Use the matrix below to translate familiar frameworks into systemic terms:

| Common framework concept | Systemic axis | Layer default | Notes |
|--------------------------|---------------|---------------|-------|
| Incident response SLA | S4 Defense | L5 Workflow | Enforce guardrails before reintroducing workflow changes. |
| Regulatory compliance (SOX, SOC2) | S6 Truth / S8 Ethics | L1 Principles / L4 Architecture | Map controls to observable proofs, then layer-specific automation. |
| Safety policy / red team reviews | S8 Ethics | L2 Objectives / L5 Workflow | Escalate only after S1–S6 are satisfied (unity, truth). |
| Product OKRs | S3 Propagation / S5 Intelligence | L2 Objectives | Link OKRs to receipts and systemic targets to demonstrate alignment. |

Steps:
1. Inventory existing policies and assign candidate S/L tokens.  
2. Document conflicts or gaps (e.g., a policy referencing “integrity” may span S4/S6).  
3. Decide whether to promote, adapt, or retire rules to maintain minimalism.  
4. Capture the final mapping in an internal guide (fork `docs/automation/ocers-systemic-mapping.md` as a template).  
5. Append governance events when the constitutional layers change.

---

## 6. Automation hooks & CI integration

- **Policy enforcement:** Port the import/placement checks (`scripts/policy_checks.sh`) into your automation pipeline.  
- **Receipts checks:** Implement a guard equivalent to `scripts/ci/check_plan_receipts_exist.py` to block merges when systemic metadata or receipts are missing.  
- **Quickstart smoke:** Recreate `scripts/ci/quickstart_smoke.sh` tailored to your environment to ensure canonical artifacts still build.  
- **Soft policies:** Use warnings for cultural adoption (e.g., referencing systemic targets in PR descriptions) before enforcing hard gates.

When migrating from OCERS-era terminology, supply a temporary `--legacy-ocers` flag in your tools to ease the transition while retraining teams.

---

## 7. Lineage, anchors, and multi-node adoption

For cross-org or decentralized deployments:
1. **Anchors:** Maintain an append-only log (JSON, blockchain, notarized ledger) capturing hash lineage, responsible steward, and previous hash reference.  
2. **Cross-node receipts:** Follow the plan `2025-09-22-decentralized-propagation-pilot`—exchange signed receipts, reconcile conflicts, and publish merge summaries.  
3. **Conflict policy:** Define how higher systemic axes resolve disagreements (e.g., S6 Truth overrides S9 Freedom).  
4. **Audit cadence:** Schedule reconciliation runs (hourly/daily) and archive the outputs to your receipt store.

---

## 8. Checklist

| Step | Status | Notes |
|------|--------|-------|
| Stakeholders briefed on S/L lattice | ☐ | Share this guide + whitepaper sections 1–3. |
| Metadata schema selected & implemented | ☐ | JSON/YAML; validated in CI. |
| Receipts signing & storage established | ☐ | Anchors registered, signatures verified. |
| Governance mapping drafted | ☐ | Document how existing policies map to S/L tokens. |
| Automation guardrails integrated | ☐ | Receipts + policy checks in pipelines. |
| Cross-node strategy (if needed) | ☐ | Reconciliation pilot complete, receipts published. |
| Adoption metrics defined | ☐ | Track % artifacts with systemic metadata, receipts coverage, latency. |

---

## 9. References

- `docs/foundation/systemic-scale.md` — canonical definitions of the systemic lattice.  
- `docs/workflow.md` — architecture gate, operator mode, DNA recursion.  
- `docs/automation/systemic-overview.md` — enforcement details inside this repo.  
- `docs/automation/systemic-residual-audit.md` — recurring audit checklist.  
- `docs/proposals/20250922t190055z__decentralized-propagation-pilot__draft.md` — blueprint for cross-node receipts.
