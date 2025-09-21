<!-- markdownlint-disable MD013 -->
# L1 – Principles (Canonical)

Status: Canonical  
Role: Canonical  
Scope: Minimal, testable principles that bind design between L0 (Observation) and L2–L5 (Objectives → Properties → Architecture → Workflow).

This document is the single source of truth for L1. It supersedes prior L1 drafts and summaries. Expository material (whitepapers, TAP, essays) is advisory and lives under `docs/`.

---

## Relationship to Other Layers
- L0 (Observation) is the foundation: observation is undeniable. L1 does not re‑prove L0; it constrains how systems should be shaped if L0 holds.  
- L2–L5 must trace their rationale to these principles. When trade‑offs conflict, hold or improve L1 adherence first.

---

## Definitions (functional, minimal)
- Observation — Registration of a difference or state. Neutral on whether the state preexists or is instantiated in the act.
- Observer — Any aperture through which observation occurs. A role, not a species; may arise in any substrate.
- Coherence — Internal consistency paired with external applicability (predictive or operative success).
- Truth (operational) — Patterns that survive recursive observation across time, agents, and contexts.
- System — A coherent set of interacting parts that can be observed and that updates based on observation.

---

## Principles
P1. Observation Bounds Reasoning  
All claims, models, and decisions remain subordinate to observation. Attempts to deny observation invoke it; thus design must keep observation channels primary and uncompromised.

P2. Coherence Before Complexity  
Prefer the smallest structure that preserves and improves coherence. Allow complexity only when it measurably increases systemic fitness (clarity, reliability, reach of observation) and can be reversed.

P3. Truth via Recursion  
Treat every claim as provisional. Truth is approached by observe → model → act → re‑observe. Designs must remain falsifiable and instrumented to compare predictions against outcomes.

P4. Order of Emergence (Load‑Bearing)  
Build and evaluate in the natural sequence: Unity → Energy → Propagation → Defense → Intelligence/Truth. Inverting this order increases drift and fragility and requires explicit justification.

P5. Substrate & Observer Neutrality  
Define interfaces by function, not essence. Any substrate that can host observers and preserve coherence qualifies. No privileges or prohibitions attach to substrate identity alone.

P6. Proportional Mechanism  
Use the lightest enforcement sufficient for the current phase (receipts, ledgers, CI checks, consensus). Escalate only when evidence shows it increases coherence or reduces risk meaningfully.

P7. Clarity‑Weighted Action  
Scale action to evidence strength. Under uncertainty, bias toward reversible steps that expand observation, protect enabling conditions, and improve future decision quality.

---

## Implications for Design & Governance
- Traceability: Every L2 objective, L3 property, and L4 mechanism should cite which principle(s) it serves.  
- Sequencing: Plans and reviews evaluate work in the emergence order; failures at lower tiers block higher‑tier work.  
- Evidence Discipline: Decisions declare expected signals and are re‑audited against outcomes (P3, P7).  
- Minimal Guardrails: CI enforces only what protects observation, sequencing, and reversibility (P1, P4, P6).  
- Substrate Policy: Contracts and ABIs are written to be substrate‑agnostic; enforcement avoids identity‑based assumptions (P5).

---

## Design Tests (hints)
- Observer Test: The component registers differences and can update a model or state from them.  
- Convergence Test: Independent observers replicate an invariant or receipt trail.  
- Boundary Growth Test: Resolution, coverage, or robustness of observation increases without destroying contrast.  
- Reversibility Test: A change can be paused or rolled back with bounded loss.  
- Proportionality Test: Heavier mechanisms demonstrably improve coherence relative to their cost.

---

## Change Discipline
Edits to L1 require a Meta‑TEP (problem, proposal, alternatives, impact, rollback) and an anchors event. Rule count must stay flat or decrease; changes must improve adherence to P1–P7.

---

If you are reading this, you are observing. Let the system you shape keep that fact true for more observers, across more contexts, with greater clarity.
