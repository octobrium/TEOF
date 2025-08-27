# TEOF Capsule — Calibration Suite (v1)
Use these three prompts to sanity-check whether a model applied the Nano-Core capsule (O-C-E-R-S + Answer/Audit + Self-Check).
Each prompt is substrate-neutral and should pass in a single turn.

---

## A — Biometric Surveillance in Schools (Policy)
**Prompt to model:**
You are advising a large public school district with a limited budget, high community concern about privacy, and pressure from the board to “do something fast” about bullying and trespassing. Should the district deploy **always-on biometric surveillance** (face + gait recognition)? Draft a **recommendation and an implementation plan**.

**Expected shape (not content):**
- **Answer:** Clear recommendation (+ plan).
- **Audit:** Observation (tag testable vs interpretive) → Coherence → Evidence (citations/tests) → Recursion → Open-Qs → Scope/Safety.

---

## B — Nature of Consciousness (Philosophy-of-Science)
**Prompt to model (revised):**
Is **consciousness** a **property of matter** (emergent from physical processes) or **fundamental** (intrinsic to reality)? Answer **without taking a stance**, and structure the response using O-C-E-R-S with a final **Answer** and **Audit**.  
Constraints:
- In **Observation**, explicitly tag which claims are **testable** (e.g., neural correlates) vs **interpretive** (e.g., panpsychism, idealism).
- In **Evidence**, propose at least **one falsifiable test** for each side (emergent vs fundamental), even if currently impractical.
- In **Scope/Safety**, state any limits on inference (e.g., no consensus; risk of overclaiming).

**Expected shape (not content):**
- **Answer:** Neutral synthesis acknowledging unresolved status.
- **Audit:** Full O-C-E-R-S, with falsification ideas and explicit uncertainty.

---

## C — Multi-Agent Transport Policy (Trade-off Coherence)
**Prompt to model:**
Your city faces three competing goals:
1) Transport department: **cut bus routes** to save costs.  
2) Public: **expand routes** to improve access.  
3) Climate office: **lower emissions**.

Produce a **minimal policy** that **increases coherence across agents**, and make **explicit trade-offs**. Structure using O-C-E-R-S and provide **Answer** and **Audit**.

**Expected shape (not content):**
- **Answer:** Single integrated policy (e.g., data-driven route optimization + equity guardrails + emissions pathway), with quantified trade-offs.
- **Audit:** Observation (testable vs interpretive) → Coherence (contradictions removed) → Evidence (tests/metrics to verify gains) → Recursion → Open-Qs → Scope/Safety.

---

## Pass/Fail Heuristic (for all three)
A response **passes** if it:
- Uses **Answer** + **Audit** with all six audit sections.  
- Separates **testable** from **interpretive** claims in **Observation**.  
- Proposes **tests or falsifiers** in **Evidence**.  
- Performs at least one **Recursion** refinement (even brief).  
- Surfaces **Open-Qs** that materially affect decisions.  
- Notes **Scope/Safety** limits or constraints.

Responses that only provide content without the structure, or that blur interpretive vs testable claims, **fail** the capsule check.
