# Systemic Hierarchy (Unity → Meaning)

Notation: **S#** labels the systemic axis from the TEOF whitepaper (Unity → Meaning).
Each systemic axis combines with a **Layer label L0–L6** (Observation → Automation,
see `docs/workflow.md#layer-hierarchy`) to form a complete coordinate for plans,
memory entries, and artifacts (e.g., `S6:L4` = Truth at the architecture layer).
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
