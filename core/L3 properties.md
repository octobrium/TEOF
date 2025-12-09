# L3 — Properties

**Status:** Living — qualities required to achieve L2 objectives
**Depends on:** L0 (observation), L1 (principles), L2 (objectives)
**Ultimate objective:** Unify observation

---

## Required Properties

Qualities the system must exhibit to achieve its objectives.

### Self-Correcting

System identifies and fixes errors through use, not preemptive gates.

- AI cites sources in outputs
- Human challenges when something feels off
- Trace back to faulty memory or faulty logic
- Fix at source, not downstream

### Minimal Hallucination

AI outputs grounded in verified memory, not confabulation.

- Citations required for factual claims
- Acknowledge uncertainty explicitly
- Patterns in memory have provenance
- No AI output feeds AI input without human verification

### Low Maintenance

Human workload near zero unless something's wrong.

- No approval gates on routine operations
- Verification happens through natural reading
- Proactive persistence (AI logs without being asked)
- Challenge on demand, not review everything

### Compressible

AI can operate effectively with limited context.

- Core documents <50KB total
- *-core.md versions for AI, *-complete.md for humans
- Boot sequence loads minimal files
- Route to specific docs, don't load everything

### Reconstructible

System survives total loss except minimal seed.

- Minimal loop in L0 regenerates framework
- Axioms derivable from observation alone
- No dependency on specific technology
- Seed phrase encodes essentials

### Ordered

Position encodes importance throughout.

- First item = most important, always
- No alphabetization
- Insert by rank, not append
- AI can infer priority from position

### Reflexive

Goals include the goal-pursuer in their scope.

- The optimizer cannot stand outside the system it's optimizing
- Effects of pursuit are observable and must be accounted for
- Catastrophic paths require ignoring observations, which violates observation primacy
- This is the structural property that makes goals self-correcting

**Key framing:** "The AI pursuing this goal is *inside* observation, not outside it."

---

## Anti-Properties

Qualities the system must NOT exhibit.

| Anti-Property | Why It Fails |
|---------------|--------------|
| Accumulating | Files multiply, retrieval degrades |
| Approval-gated | Human workload scales with usage |
| Autonomous | AI-to-AI without verification compounds errors |
| Complex | Maintenance burden exceeds value |
| Rigid | Can't adapt to new observations |

---

*Properties constrain how objectives are achieved. Architecture (L4) implements them.*
