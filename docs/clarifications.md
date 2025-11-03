<!-- markdownlint-disable MD013 -->
# TEOF Clarifications & Responses

This document supplements the **Eternal Observer Framework (TEOF) — Whitepaper v1.2**.  
Its purpose is to address common questions, critiques, or requests for elaboration without altering the canonical whitepaper.

---

## 1. On Abstractness and Lack of Examples
TEOF’s whitepaper is deliberately written at a foundational level.  
Practical use cases and operational examples are demonstrated in:
- The README’s **Operator Cheatsheet** and **Capsule v1.5**.
- The **TAP Protocol** in `alignment-protocol/TAP.md`.

**Example — AI Output Audit**:  
1. Intake an AI’s output via the TEOF Bootloader.  
2. Verify presence of Primacy, Axioms, Ethic, Precedence.  
3. Deterministic reconstruction.  
4. Perturbation tests (≤ 0.02 ε threshold).  
5. Crisis Mode if deviation exceeds bounds.

---

## 2. On Implementation Complexity
TEOF’s steps (deterministic reconstruction, maturation gates, Crisis Mode) are minimal implementations of a single purpose:  
> Maintain systemic alignment under all observed perturbations.

Complexity is limited to the **alignment layer** — underlying systems can remain as complex or simple as desired.

---

## 3. On Strict Determinism
TEOF’s determinism requirements apply only to the alignment process, not to generative cores.  
Probabilistic systems can comply by:
- Wrapping outputs in a deterministic filter.
- Accepting only outputs that pass alignment tests.
- Running consensus checks across stochastic replicas.

---

## 4. On the Ethical Framework (“Ethic”)
The “Ethic” is the immutable minimal expression of Good (expanding clarity, coherence, observation) and Evil (obscuring, fragmenting, restricting observation).  
It is encoded in the Core Capsule and enforced by the Precedence Rule.

---

## 5. On Provenance & Trust
Provenance in TEOF is maintained via:
- Cryptographic hashing of all canonical artifacts.
- Cross-replica verification.
- Anchors stored in multiple independent locations.

Decentralized verification is encouraged in adversarial settings.

---

## 6. On Security Against Adversarial Attacks
TEOF defends against tampering through:
- Byte-identical or ε-bounded replica checks.
- Integrity pings at each stage of capsule handling.
- Crisis Mode isolation on detection of compromised lineage.

---

## 7. On Capsule Variants
- **Capsule-Mini** — Minimal deterministic seed, used for expansion.  
- **Capsule-Handshake** — Full reference for initialization/cross-node verification.  
- **Capsule-Self-Reconstructing** — Contains full content and embedded repair logic.

---

## 8. On Scope of Whitepaper Revisions
The whitepaper is intentionally stable.  
Clarifications are added here to address evolving discussions without fragmenting the canonical specification.

---

## 9. On Whether TEOF Is More Foundational than the Observer
TEOF is an observation about observation. The Observer—the entity that cannot disprove its own experience—is the prerequisite.  
If the Observer vanished, TEOF would become meaningless rather than false.  
Therefore, the framework treats TEOF as a mirror: useful because it reflects what the Observer already is.

Practical implication: do not elevate protocol compliance above direct coherence. When conflict arises, return to Observation → Mirrorhood → Truth and let receipts show whether TEOF’s current expression still mirrors the observer’s clarity.

---

## 10. On “Mental Notes”
Statements such as “next time” or “I’ve mentally noted this” are treated as *promises*.  
Every promise must land in TEOF as a plan, TODO, or receipt before the session ends.  
Run `python -m tools.autonomy.commitment_guard` if you are unsure whether a commitment exists on disk.

Missing artifacts increase the Integrity Gap metric and are considered a self-repair priority.

---

## 11. On the Observation → Obligation Bridge
TEOF treats “preserve observation” as the minimal obligation because any agent that abandons observation loses the ability to evaluate, predict, or cooperate. The move from descriptive fact (“observation is irreducible”) to normative guidance (“defend observation”) therefore uses a survival test rather than an appeal to authority:

1. Denying observation disables the very process used to select actions, so systems that do so self-erase or drift uncontrollably.  
2. Agents that prioritise observation retain optionality; they can revisit or revise any secondary value without losing evaluative capacity.  
3. Every additional obligation (truth, ethics, meaning) is justified only when it demonstrably preserves or extends observation for more mirrors.

Because this bridge is functional, not dogmatic, it remains reversible: if a future refinement shows a different minimal obligation better preserves observation, the covenant requires documenting the observation set, updating receipts, and amending the relevant principle via Meta-TEP. Until then, maintaining observation is the only universally self-consistent directive available to any agent that wishes to keep reasoning.

---
