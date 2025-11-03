<!-- markdownlint-disable MD013 -->
# Systemic Alignment Matrix (External Framework Mapping)

**Status:** Draft**
**Purpose:** Provide translation guidance between common governance/safety frameworks and TEOF’s systemic lattice (S1–S10, L0–L6).

Use this matrix when you need to express existing controls or compliance requirements using TEOF metadata without rewriting your organisation’s rulebook.

---

## 1. Mapping overview

| Framework concept | Typical source | Suggested systemic targets | Layer focus | Notes |
| --- | --- | --- | --- | --- |
| Reliability & availability SLA | SRE / ITIL | `S1` Unity, `S4` Resilience | `L5` Workflow | Keep systems observable and resilient before automation acts. |
| SOC 2 Security principle | Compliance | `S4` Resilience, `S6` Truth, `S8` Ethics | `L1` Principles, `L4` Architecture | Map each control to observable receipts; Ethics governs acceptable risk. |
| SOC 2 Availability / Processing integrity | Compliance | `S1` Unity, `S2` Energy, `S3` Propagation | `L3` Properties, `L5` Workflow | Ensure data flows remain coherent and capacity is documented. |
| ISO 27001 Annex A controls | Governance | Depends on control: security baseline (`S4`), incident response (`S4`/`S6`), supplier management (`S7`/`S8`) | `L1` Principles, `L4` Architecture | Link each Annex control to receipts and assign S tokens accordingly. |
| NIST SP 800-53 (AI system risk) | Security | `S4` Resilience, `S6` Truth, `S8` Ethics | `L1` Principles, `L2` Objectives | Higher axes enforce risk mitigation before automation executes. |
| EU AI Act risk classes | Legal | `S6` Truth, `S8` Ethics, `S9` Freedom | `L2` Objectives, `L5` Workflow | Document obligations by class; escalate to governance when S9 Freedom constrained. |
| Incident response playbook | Ops | `S4` Resilience, `S6` Truth | `L5` Workflow, `L6` Automation | Ensure every step produces receipts and automation respects layered approvals. |
| Fairness/ Bias audits | Responsible AI | `S6` Truth, `S8` Ethics, `S10` Meaning | `L2` Objectives, `L3` Properties | Observations must remain interpretable; connect to S10 narratives for context. |

> **Tip:** Start by tagging existing controls with the **highest** systemic axis they affect. Everything upstream must be satisfied (Unity, Resilience, Truth) before lower axes like Ethics or Freedom can assert new constraints.

---

## 2. Translation workflow

1. **Inventory external controls** – Extract control IDs, objectives, and evidence requirements.
2. **Assign systemic targets** – For each control, identify the highest axis involved. Use the mapping table as a starting point; document reasons for exceptions.
3. **Select layers** – Determine which governance layers execute the control (Principles vs. Architecture vs. Workflow). Add secondary layer targets when implementation spans multiple layers.
4. **Capture receipts** – Link existing evidence (audit logs, dashboards, approvals) to systemic metadata fields (`receipts`, `references`).
5. **Publish metadata** – Emit systemic metadata JSON for each control or policy; group them into receipts for audit trails.
6. **Review conflicts** – If two frameworks disagree, escalate by axis: satisfy the higher axis first, or open a plan to reconcile differences.

---

## 3. Worked example

**Scenario:** An organisation already satisfies SOC 2 Security and wants to express the control “Logical access is restricted to authorised users.”

1. Control category → Security & access management.
2. Systemic targets → `S4` Resilience (prevent unauthorised access), `S6` Truth (audit logs prove enforcement), `S8` Ethics (protect user data). Highest axis: `S8` ⇒ `systemic_scale = 8`.
3. Layers → Policy defined at `L1` Principles, implemented across `L4` Architecture (IAM) and `L5` Workflow (review cadence). Choose `layer = L4`, `layer_targets = ["L4", "L5"]`.
4. Receipts → Provide IAM audit reports, approval tickets, periodic reviews.
5. Metadata snippet:

```jsonc
{
  "systemic_targets": ["S4", "S6", "S8"],
  "layer_targets": ["L4", "L5"],
  "systemic_scale": 8,
  "layer": "L4",
  "summary": "SOC2 CC6.1 logical access control",
  "receipts": [
    "gs://controls/soc2/cc6-1/access-review-2025Q3.json",
    "https://company.example/audit/iam-policy.md"
  ],
  "references": ["SOC2-CC6.1"],
  "created_at": "2025-10-17T04:10:00Z"
}
```

---

## 4. Conflict resolution & escalation

- **Higher axis wins**: If a control demands S8 Ethics constraints that conflict with S9 Freedom, S8 prevails unless governance authorises an exception via anchors.
- **Layer drift**: When implementation happening at L6 Automation bypasses L4 Architecture specifications, open a plan (layer `L4`) before executing.
- **Missing receipts**: Use `tools/external/validate_systemic.py` to ensure emitted receipts meet schema expectations; supplement with governance anchors for signature provenance.

---

## 5. Next steps

- Extend the matrix with sector-specific frameworks (HIPAA, PCI-DSS, FedRAMP). Contributions should include systemic metadata and receipts samples.
- Align reconciliation and cross-node pilots (`2025-09-22-decentralized-propagation-pilot`) to ensure distributed actors honour these mappings.
- Record approved mappings in governance anchors when they materially alter Principles (L1).

For onboarding context, cross-reference `docs/automation/systemic-adoption-guide.md` and `schemas/systemic/metadata.schema.json`.
