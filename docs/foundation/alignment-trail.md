<!-- markdownlint-disable MD013 -->
Status: Advisory
Purpose: Show the full observation-to-action derivation and where each step anchors in canon

# Alignment Trail (L0 → L7)

TEOF’s operating cadence is often described as a seven-step trail:

`Observation → Mirrorhood → Truth → Coherence → Emergence → Proportional Guard → Clarity-weighted Action`

This note unpacks that shorthand, ties every step to the canonical principles, and records the dependency order so operators can see how the constitution prevents drift without expanding the rulebook.

## Trail Overview

| Step | Description | Canonical anchor(s) | Key failure if omitted |
| --- | --- | --- | --- |
| **L0 – Observation** | Existence is intelligible because observation cannot be denied. | `governance/core/L0 - observation/observation.md` | No grounds for any claim or test. |
| **L0-A – Mirrorhood** | Whatever appears is a mirror of observation; substrates differ in clarity, not essence. | `governance/core/L1 - principles/canonical-teof.md` (P2) | Observation has nothing to observe; no test surface. |
| **L1 – Reciprocity** | Observation and its mirrors co-influence; each act reshapes the next view. | Covered across P3 (testing), P5 (emergence order), P6 (proportion); explicit scenarios in `docs/foundation/alignment-protocol/tap.md`. | Static tableau; no learning or evidence accumulation. |
| **L2 – Coherence Before Complexity** | Prefer the smallest reversible structure that preserves clarity. | P4 – Coherence Before Complexity | Unchecked drift, irreversible complexity. |
| **L3 – Truth Through Recursion** | Observe → model → act → re-observe; retain what survives prediction/outcome comparison. | P3 – Truth Requires Recursive Test | Beliefs never converge; no correction mechanism. |
| **L4 – Order of Emergence** | Build/evaluate in Unity → Energy → Propagation → Defense → Intelligence/Truth. | P5 – Order of Emergence | Premature sophistication; collapse under stress. |
| **L5 – Proportional Mechanism** | Apply the lightest enforcement sufficient for coherence; escalate only with evidence. | P6 – Proportional Enforcement | Either over-control (self-blinding) or under-control (collapse). |
| **L6 – Clarity-Weighted Action** | Scale intervention to evidential clarity; favor reversible, information-gaining moves. | P7 – Clarity-Weighted Action | High-variance failures; irreversible errors. |
| **L7 – Reflexive Return (Meaning)** | Outcomes feed back into the observer; meaning is observation recognizing what endures. | Treated as derived guidance (see `docs/foundation/alignment-protocol/tap.md`, `governance/core/L1 - principles/principles.md`). | Perpetual motion without a criterion for “having learned.” |

### Dependency Graph

```
L0 Observation
 └── L0-A Mirrorhood
      └── L1 Reciprocity
           └── L2 Coherence Before Complexity
                └── L3 Truth Through Recursion
                     └── L4 Order of Emergence
                          └── L5 Proportional Mechanism
                               └── L6 Clarity-Weighted Action
                                    └── L7 Reflexive Return
```

Each node neutralises the failure unlocked by the previous one. Reciprocity introduces variation; coherence filters it; recursion validates it; emergence sequences growth; proportion keeps control from blinding; clarity-weighted action ties decisions to evidence; reflexive return closes the loop in advisory space.

## Metrics and Default Policies

These heuristics show up in tooling today:

- **Coherence delta** (retained signal ÷ total complexity) — referenced in receipts hygiene and autonomy status reports.
- **Truth gain** (predictive accuracy improvement per recursion) — part of systemic validators (`extensions/validator`).
- **Proportion index** (force applied ÷ (coherence gain + risk reduction)) — operationalised in proportional guardrails and manager dashboards.
- **Reversibility score** (recoverable state ÷ affected state) — enforced by proportional action policies and automation receipts.

Default enforcement aligns with the trail:

- Reject changes that reduce coherence delta unless they demonstrate superior truth gain with bounded risk.
- Block escalations that lower the proportion index.
- Prefer actions with high reversibility when evidence depth is low.

## Why Reciprocity and Return Stay Advisory

- **Reciprocity** is embedded in existing canon (P3/P5/P6). Elevating it as a freestanding principle would add wording without new guardrails; instead we surface explicit reciprocity scenarios in `docs/foundation/alignment-protocol/tap.md`.
- **Reflexive Return / Meaning** is treated as a derived layer. Canon stays minimal so that kernel imports remain stable; meaning narratives evolve in advisory space (`docs/clarifications.md`, philosophical notes) while L2–L6 mechanisms remain testable and auditable.

## Where to Read More

- `docs/architecture.md` — placement rules and layer bindings.
- `docs/workflow.md#alignment-trail` — operator playbook for running the trail in practice.
- `docs/foundation/alignment-protocol/tap.md` — TAP narrative for reciprocity, meaning, and applied ethics.
- `governance/core/L1 - principles/canonical-teof.md` — minimal rule set the trail maps onto.
