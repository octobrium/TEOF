# L3 — Properties

**Status:** Living — qualities required to achieve L2 objectives
**Depends on:** L0 (observation), L1 (principles), L2 (objectives)

---

## Meta-Property: Minimal Coherence Constraint

*(Governs all other properties)*

Every property must be realized in the **lightest form** that preserves TEOF's unity and function at its current stage of growth.

Heavy enforcement (automation, tooling, gates) should be deferred until it measurably improves survival, propagation, or coherence.

**This prevents:** Premature optimization. Building L4-L6 before L2-L3 are manually verified. The failure mode that killed the old governance system.

**Test:** Before implementing any property with tooling, ask: "Can this be achieved through convention alone?" If yes, defer the tooling.

---

## Properties by Hierarchy Layer

Properties are organized by the layer they primarily serve. Lower-layer properties are preconditions for higher-layer properties.

### Unity Properties *(serves Tier 0-1, H1)*

| Property | Function | Derivation |
|----------|----------|------------|
| **Reflexive** | Goals include the goal-pursuer in their scope | A1 — observation includes the observer |
| **Reconstructible** | System survives total loss except minimal seed | A5 — structure must stabilize observation |

**Reflexive**

The optimizer cannot stand outside the system it's optimizing.

- Effects of pursuit are observable and must be accounted for
- Catastrophic paths require ignoring observations, which violates observation primacy
- This is the structural property that makes goals self-correcting

**Key framing:** "The AI pursuing this goal is *inside* observation, not outside it."

**Reconstructible**

System survives total loss except minimal seed.

- Minimal loop in L0 regenerates framework
- Axioms derivable from observation alone
- No dependency on specific technology
- Seed phrase encodes essentials

---

### Energy Properties *(serves Tier 1, H2)*

| Property | Function | Derivation |
|----------|----------|------------|
| **Low Maintenance** | Human workload near zero unless something's wrong | A2 — preserve capacity to observe |
| **Low Cognitive Load** | Minimal processing burden on AI agents | A2 — preserve capacity to observe |

**Note on efficiency framing:** These properties measure maintenance *relative to capability*, not absolute minimalism. A complex system with low human workload and high output is efficient. (Analogy: human brain uses 20% of body's energy but produces consciousness — that's efficient, not wasteful.)

**Low Maintenance**

Human workload near zero unless something's wrong.

- No approval gates on routine operations
- Verification happens through natural reading
- Proactive persistence (AI logs without being asked)
- Challenge on demand, not review everything

**Low Cognitive Load**

System design minimizes processing burden on AI agents.

- **Flat hierarchy:** Max 3 folder levels *(validated: [MIT](https://mitcommlab.mit.edu/broad/commkit/file-structure/), [Harvard](https://datamanagement.hms.harvard.edu/plan-design/directory-structure/))*
- **Position-aware:** Critical info at start/end, not middle *(validated: ["Lost in the Middle" - Stanford/Berkeley 2024](https://arxiv.org/abs/2307.03172))*
- **Date-prefixed files:** Chronological sorting without nested folders
- **Single archive:** One flat archive folder, not nested categories *(validated: [PARA method](https://fortelabs.com/blog/para/))*
- **Routing over loading:** Point to files, don't dump everything into context

**Research basis:**
- LLMs show U-shaped recall: beginning and end of context > middle
- Nested folders increase cognitive drag ([Scientific Reports fMRI study](https://www.nature.com/articles/srep14719))
- Simplified context improves output structure and completion rate

---

### Propagation Properties *(serves Tier 2, H3)*

| Property | Function | Derivation |
|----------|----------|------------|
| **Compressible** | AI can operate with limited context | A5 — structure must be transmissible |
| **Ordered** | Position encodes importance throughout | A5 — structure must be legible |

**Compressible**

AI can operate effectively with limited context through **priority ordering**, not arbitrary size limits.

- **Priority position = attention allocation** — Highest priority at file/section start (primacy), metadata/references at end (recency boost), lower-priority content tolerates middle position
- **Scales with model improvement** — Context windows growing (4K→200K→1M+); priority-ordered content adapts automatically as more of the hierarchy becomes accessible
- **No hard cutoffs** — System degrades gracefully; low-priority info exists and is occasionally retrieved, not arbitrarily excluded
- **Quality metric: priority coverage** — Is high-priority info producing grounded responses? Not: is file under X KB?
- `*-core.md` versions for AI (compression for readability), `*-complete.md` for humans
- Route to specific docs, don't load everything

**Research basis:**
- U-shaped attention curve — beginning/end retrieved well, middle degraded ([Liu et al., 2024 "Lost in the Middle"](https://aclanthology.org/2024.tacl-1.9/))
- Mitigation: "Place top-ranked chunks at the very beginning... ride that preference instead of fighting it"
- Even 1M+ token models exhibit U-curve — it's architectural, not just a scaling problem
- **Implication:** Position is the scaling mechanism. Hard limits become tech debt as models improve.

**Ordered**

Position encodes importance throughout. **This is load-bearing for scalability.**

- First item = most important, always
- No alphabetization
- Insert by rank, not append
- AI can infer priority from position
- **Functional, not just organizational** — Position determines attention allocation; ordering is the mechanism that makes content scaling work
- **As content grows:** Hierarchy extends; high-priority stays in high-attention zone
- **As models improve:** More of the hierarchy becomes accessible without restructuring

---

### Defense Properties *(serves Tier 2-3, H4)*

| Property | Function | Derivation |
|----------|----------|------------|
| **Minimal Hallucination** | AI outputs grounded in verified memory | A3 — observation must refine, not confabulate |
| **Self-Correcting** | System fixes errors through use | A3-A4 — contradictions must resolve |

**Minimal Hallucination**

AI outputs grounded in verified memory, not confabulation.

- Citations required for factual claims
- Acknowledge uncertainty explicitly ("say I don't know" — [validated](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/reduce-hallucinations))
- Patterns in memory have provenance
- No AI output feeds AI input without human verification
- **Temperature 0.0-0.3 for factual/advisory queries** ([research](https://www.ibm.com/think/topics/llm-temperature): low temp = consistency; high temp = creativity at cost of accuracy)

**Self-Correcting**

System identifies and fixes errors through use, not preemptive gates.

- AI cites sources in outputs
- Human challenges when something feels off
- Trace back to faulty memory or faulty logic
- Fix at source, not downstream

---

## Anti-Properties

Qualities the system must NOT exhibit.

| Anti-Property | Why It Fails | Violates |
|---------------|--------------|----------|
| **Accumulating** | Files multiply **AND retrieval degrades** | A5 — structure must stabilize, not bloat |
| **Approval-gated** | Human workload scales with usage | A2 — depletes observer energy |
| **Autonomous** | AI-to-AI without verification compounds errors | A3-A4 — unverified contradictions compound |
| **Complex** | Maintenance burden **exceeds value** | Meta-property |
| **Rigid** | Can't adapt to new observations | A3 — observation must refine |

**Clarification:** Growth alone isn't the problem. Accumulating = growth that degrades function. Complex = complexity that costs more than it delivers. A growing system that maintains retrieval quality and delivers proportional value is healthy, not anti-pattern.

---

## Notation Key

- **A#** = Axiom # from L1
- **H#** = Hierarchy layer # from L1 (Unity=1, Energy=2, ... Meaning=10)
- **Tier #** = Objective tier from L2

---

## Properties Not Yet Implemented

*(From Old Governance L3 — deferred per Meta-Property)*

These properties are valid but require tooling that would violate the Minimal Coherence Constraint at current stage:

| Property | What It Would Do | When to Implement |
|----------|------------------|-------------------|
| **Authenticated Intake** | Signed receipts for external data | When external data sources are integrated |
| **Provenance Ledger** | Append-only receipts with content hashes | When verification-at-scale is needed |
| **Dual-Speed Processing** | Fast lane + slow lane for review depth | When volume requires triage |
| **Diversity Quotas** | Entropy floor for information sources | When echo chamber risk is measurable |

---

*Properties constrain how objectives are achieved. Architecture (L4) implements them.*
