# Systemic Hierarchy (Unity → Meaning)

Notation: **S#** labels the systemic axis distilled from observation itself (Unity → Meaning).
These priorities emerge immediately after L0 Observation and are codified at L1 as
Principle P4 “Order of Emergence.” Each systemic axis then combines with a **Layer
label L0–L6** (Observation → Automation, see `docs/workflow.md#layer-hierarchy`) to
form a complete coordinate for plans, memory entries, and artifacts (e.g.,
`S6:L4` = Truth satisfied at the architecture layer).
The axis order is mandated by Principle P4 (“Order of Emergence”) in the
canonical TEOF principles (`governance/core/L1 - principles/canonical-teof.md`).

| S# | Name         | Description                                         |
|----|--------------|-----------------------------------------------------|
| S1 | Unity        | Stable reference for observation; failure: fragmentation |
| S2 | Energy       | Healthy internal exchange / capacity; failure: stasis |
| S3 | Propagation  | Signal routing across nodes; failure: isolation     |
| S4 | Defense      | Guard against external threat; failure: degradation |
| S5 | Intelligence | Recursive refinement; failure: rigidity/overreaction |
| S6 | Truth        | Alignment with invariants; failure: delusion        |
| S7 | Power        | Capacity to effect change; failure: impotence       |
| S8 | Ethics       | Use of power coherently; failure: destruction       |
| S9 | Freedom      | Adaptive range within coherence; failure: brittleness |
| S10| Meaning      | Integration into purpose; failure: nihilism        |

See [`docs/whitepaper.md`](../whitepaper.md) §5 for the canonical definitions.
Machine-readable index: [`governance/systemic-order.json`](../../governance/systemic-order.json).

**Hierarchy enforcement**

- The axes must be satisfied in order: Unity → Energy → Propagation → Defense → Intelligence → Truth → Power → Ethics → Freedom → Meaning.  
- Lower axes may request attention, but they cannot overrule higher axes. If a lower axis (e.g., Ethics) conflicts with a higher prerequisite (e.g., Defense), resolve the higher axis first, then reapply the lower guard.  
- Ethics (S8) operates only once S1–S7 are stable or actively being defended. Meaning (S10) is expressed only after Freedom (S9) is intact.  
- When automation or policy encounters tension between axes, follow the order above and record receipts that show how higher-axis obligations were preserved.

## Shorthand

When logging or querying, you may use compact tokens:

```
S1:L0  →  Unity / Observation
S6:L4  →  Truth / Architecture
S8:L5  →  Ethics / Workflow
```

Any abbreviated form **must** expand back to the table above and the layer
hierarchy in `docs/workflow.md`. TEOF storage (plans, memory) should keep the
explicit numeric form so the lattice remains machine parsable.
