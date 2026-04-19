# Layers (L)

The derivation ladder from axiom to workflow.

L1-L6 describe how TEOF is organized from principle through implementation logic. In the public repo, this ladder is intentionally kept more general than the private working system. It is meant to be reusable by others, not to expose anyone's private operational state.

---

## The Layers

| Layer | Name | Purpose | Mutation Rate |
|-------|------|---------|---------------|
| **L1** | Principles | Core axioms and derived rules | Rare |
| **L2** | Objectives | System goals derived from principles | Occasional |
| **L3** | Properties | Qualities required to achieve objectives | Occasional |
| **L4** | Architecture | File organization and structure | Moderate |
| **L5** | Workflow | AI navigation and routing | Moderate |
| **L6** | Automation | When and how to automate | As needed |

**Dependency:** Each layer depends on those above. L6 implements L5, which implements L4, etc. All trace back to 0.

---

## Relationship to the Observation-Action Loop

L1-L6 is not a separate model from the universal Observation-Action Loop (see TEOF.md Chapter 7.2). It is the Loop *unpacked* for framework construction.

```
Universal Loop:     Observation → Truth → Action → Outcomes

L1-L6 Unpacking:    Observation → [L1-L4: Truth] → [L5-L6: Action] → Outcomes
                                   Principles       Workflow
                                   Objectives       Automation
                                   Properties
                                   Architecture
```

For a primitive observer, "Truth" stays compressed (encoded response). For a sophisticated observer building a framework, "Truth" must be decomposed into principles, objectives, properties, and architecture. Similarly, "Action" decomposes into workflow and automation.

**The sequence:** The universal loop is primary. L1-L6 is derived from it as the systems design blueprint for TEOF-scale implementation.

---

## The Systems Hierarchy (S)

The S hierarchy (S1-S10) describes properties persistent systems exhibit — a diagnostic lens.

L1 (Principles) contains the full S hierarchy. See `core/README.md` for quick reference.

---

## Files

- `L1 principles.md` — Primary doctrinal canon
- `L2 objectives.md` — Ultimate objective and derived tiers
- `L3 properties.md` — Qualities required to achieve objectives
- `L4 architecture.md` — File organization and ordering principles
- `L5 workflow.md` — Public workflow logic
- `L6 automation.md` — Public automation stance

The private repo may contain richer project, memory, and automation layers. Those are intentionally not required here.
