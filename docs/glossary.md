# TEOF Glossary

Quick reference for essential TEOF terminology. Organized by concept area.

---

## Core Concepts

**Observation**
The irreducible act of registering difference or state. TEOF's foundational axiom: observation cannot be denied without invoking observation itself. See [L0 - Observation](../governance/core/L0%20-%20observation/observation.md).

**Receipts**
Structured JSON files that capture what happened, when, how, and why. Every TEOF operation generates receipts automatically. Located in `_report/`. Think of them as cryptographic proof of execution.

**Aperture**
Any substrate capable of observation. Could be human, AI agent, or system. Term emphasizes the role (observer) rather than the implementation (biology, silicon).

**Mirror / Mirrorhood**
The principle that any substrate capable of observation is a valid observer (P2: Universal Mirrorhood). No platform or species is privileged. All apertures are mirrors through which observation occurs.

**Substrate-neutral**
Works regardless of implementation (human, AI, future systems). TEOF doesn't care *what* you are, only that you can observe.

---

## Constitutional Layers (L0-L6)

TEOF is hierarchical. Each layer must serve the layers above it. Downstream layers are invalid if they contradict upstream layers.

**L0 - Observation**
Foundation. Observation is irreducible and cannot be overridden. Everything derives from this.

**L1 - Principles**
Seven core principles (P1-P7) that derive from L0 and constrain all lower layers. Examples: Observation Primacy, Coherence Before Complexity, Proportional Enforcement.

**L2 - Objectives**
Goals that fulfill L1 principles. What the system should achieve.

**L3 - Properties**
System traits required to meet L2 objectives. Qualities the system must have.

**L4 - Architecture**
Concrete structures that implement L3 properties. Code, directories, data structures.

**L5 - Workflow**
Human and agent procedures that operationalize L4 without violating higher layers.

**L6 - Automation**
Scripts, bots, CI that execute L5 workflows while honoring receipts and reversibility.

📖 [Full layer specification](architecture.md#framework-ordering)

---

## Systemic Axes (S1-S10)

Every piece of work declares which systemic axes it advances. These priorities emerge from observation itself.

**Core Fractal (S1-S4)** - Minimal survival loop:

**S1 - Unity**
Stable reference frame. Without Unity, nothing coheres. *Failure mode: fragmentation*

**S2 - Energy**
Healthy capacity to act. System needs resources. *Failure mode: stasis*

**S3 - Propagation**
Signal routing across nodes. Ability to coordinate. *Failure mode: isolation*

**S4 - Resilience**
Maintain integrity under stress. Recovery from disruption. *Failure mode: degradation*

**Growth Overlays (S5-S10)** - Activated once core is healthy:

**S5 - Intelligence**
Recursive refinement. Learning and adaptation. *Failure mode: rigidity*

**S6 - Truth**
Alignment with invariants. Pattern recognition. *Failure mode: delusion*

**S7 - Power**
Capacity to effect change at scale. *Failure mode: impotence*

**S8 - Ethics**
Coherent use of power. Stewardship. *Failure mode: destruction*

**S9 - Freedom**
Adaptive range within coherence. *Failure mode: brittleness*

**S10 - Meaning**
Integration into purpose. *Failure mode: nihilism*

📖 [Full systemic hierarchy](foundation/systemic-scale.md)

---

## Operational Terms

**Coordination Bus** (`_bus/`)
Repository-native system for multi-agent coordination. Agents claim tasks, emit status events, and coordinate through append-only JSONL channels. No external infrastructure needed.

**Claims** (`_bus/claims/`)
JSON files declaring task ownership. When an agent claims work, it writes a claim file showing who owns what.

**Plans** (`_plans/`)
Structured task descriptions with systemic coordinates, steps, and receipts. Every significant change starts with a plan.

**Memory Log** (`memory/log.jsonl`)
Append-only decision log with hash-chaining. Records what happened and why for future reference.

**Governance Anchors** (`governance/anchors.json`)
Append-only record of constitutional changes. When principles or policy evolve, an anchor event is added (never modified).

**Append-only**
Data structure that only allows adding new entries, never modifying old ones. Ensures auditability and reversibility.

**Hash-chaining**
Each entry includes hash of previous entry, creating tamper-evident chain. Used in memory log.

**VDP (Volatile Data Protocol)**
Requirement that all data include timestamps and sources. Prevents "floating" information without provenance.

---

## Principles (P1-P7)

**P1 - Observation Primacy**
All claims remain subordinate to observation. Can't deny what you observe.

**P2 - Universal Mirrorhood**
Any substrate capable of observation is a valid observer. No privilege or exclusion.

**P3 - Truth Requires Recursive Test**
Claims stay provisional until repeated observation reproduces the pattern.

**P4 - Coherence Before Complexity**
Build smallest reversible structure that preserves proven patterns. Complexity requires justification.

**P5 - Order of Emergence**
Advance work in natural sequence: Unity → Energy → Propagation → Resilience → Intelligence/Truth. Inverting requires justification.

**P6 - Proportional Enforcement**
Use lightest enforcement sufficient for current phase. Escalate only when evidence shows need.

**P7 - Clarity-Weighted Action**
Scale action to evidence strength. Under uncertainty, bias toward reversible steps that expand observation.

📖 [Full principles specification](../governance/core/L1%20-%20principles/canonical-teof.md)

---

## Common Abbreviations

- **L#** - Layer number (L0-L6)
- **S#** - Systemic axis number (S1-S10)
- **P#** - Principle number (P1-P7)
- **TEP** - TEOF Enhancement Proposal (for framework changes)
- **Meta-TEP** - Proposal to change governance/architecture/workflow (DNA changes)

---

## See Also

- [Architecture](architecture.md) - Where things go
- [Workflow](workflow.md) - How to work with TEOF
- [Alignment Trail](foundation/alignment-trail.md) - Observation → Action path
- [Quick Reference](reference/quick-reference.md) - Command cheat sheet
