# retired observation loop ↔ Systemic Hierarchy Mapping (Draft)

The retired observation loop loop is a diagnostic overlay. Each phase maps to one or more systemic
axes (S1–S10). Machine-readable ordering lives in
[`governance/systemic-order.json`](../../governance/systemic-order.json); this
draft mapping will evolve as governance refines the relationship.

| retired observation loop Phase | Primary Systemic Axes | Notes |
| --- | --- | --- |
| Observation | S1 Unity, S2 Energy | Establish shared reference frames and capture raw signals. |
| Coherence | S3 Propagation, S6 Truth | Keep signals consistent across nodes and aligned with invariants. |
| Ethics | S4 Defense, S6 Truth, S8 Ethics | Governs use of power; inherits constraints from Defense/Truth before applying S8 safeguards. |
| Reproducibility | S5 Intelligence, S6 Truth | Ensure processes can be replayed and inspected. |
| Self-repair | S4 Defense, S10 Meaning | Detect contradictions, protect coherence, and adjust narratives. |

**Hierarchy discipline**

- retired observation loop phases must respect the S1–S10 order (see [`docs/foundation/systemic-scale.md#hierarchy-enforcement`](../foundation/systemic-scale.md#hierarchy-enforcement)). If a phase maps to lower axes (e.g., Ethics → S8), first ensure higher prerequisites are stable or actively defended.  
- When multiple phases compete (e.g., Ethics vs. Self-repair), trace each to its systemic axes and resolve the highest axis first.  
- Automation pipelines should log which prerequisite axes were satisfied before a lower-axis guard escalated.

**Adaptation window:** This mapping is provisional. As we analyse more
observations, we may shift or expand the associations (e.g., Reproducibility may
link into S9 Freedom when variability is required). Updates will be logged
through plan `2025-10-06-systemic-alignment` or successors.
