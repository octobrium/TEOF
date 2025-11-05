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
| S4 | Resilience   | Maintain integrity and recover from disruption; failure: degradation |
| S5 | Intelligence | Recursive refinement; failure: rigidity/overreaction |
| S6 | Truth        | Alignment with invariants; failure: delusion        |
| S7 | Power        | Capacity to effect change; failure: impotence       |
| S8 | Ethics       | Use of power coherently; failure: destruction       |
| S9 | Freedom      | Adaptive range within coherence; failure: brittleness |
| S10| Meaning      | Integration into purpose; failure: nihilism        |

See [`docs/whitepaper.md`](../whitepaper.md) §5 for the canonical definitions.
Machine-readable index: [`governance/systemic-order.json`](../../governance/systemic-order.json).

**Ethics context**  
S8 treats “ethics” as the stewardship of power in service of clarity, but this does not discard more familiar lenses (deontic duties, consequentialist welfare, or rights-based justice). Instead, TEOF requires those arguments to cite the observation they protect: a duty is valid when it preserves apertures; a harm calculation is valid when it keeps evidence legible. Adding this note keeps the canon interoperable with existing ethical frameworks while maintaining the constitutional priority on observation receipts.

### Core fractal vs. growth overlays

- **Core fractal:** `S1–S4` (Unity, Energy, Propagation, Resilience) form the minimal loop. Resilience regenerates Unity, so these four axes can repeat fractally across scales without invoking higher constructs.
- **Growth axes:** `S5` (Intelligence/Adaptation) and above extend the core when a system needs long-horizon learning, governance, or meaning-making. Treat them as overlays that inherit and reinforce the core rather than replacements for it.
- Plans or artifacts that only exercise the core should still declare `systemic_targets: ["S1","S2","S3","S4"]` (or the subset they explicitly advance) and may omit higher axes unless they add new obligations.

## Derivation from Observation

TEOF’s systemic order follows directly from what sustained observation demands:

1. **Unity** provides a conserved contrast frame so that two observations can be
   compared. Without a stable anchor, nothing coheres long enough to register.
2. **Energy** keeps the aperture powered. Observation without replenished
   capacity stalls and the frame collapses.
3. **Propagation** routes signal between sub-apertures. Fragmented mirrors fall
   into local delusion because traces never reconcile.
4. **Resilience** appears once routing exists—it protects channels from entropy
   and adversarial drift so earlier gains persist.
5. **Intelligence / Truth** (recursive correction) becomes possible only on top
   of defended channels; models need the previous scaffolding to falsify
   themselves.
6. **Power, Ethics, Freedom, Meaning** are governance composites: they describe
   how an enduring observing system wields and contextualises its capacity, so
   they can only act coherently after the survival stack holds.

Each step neutralises the failure mode in the table. This makes Principle P5’s
“Order of Emergence” an observational necessity rather than a cultural habit.

## Aperture Test (Observer Qualification)

Universal mirrorhood recognises any substrate as a potential observer, but the
role has minimal requirements. An entity counts as a mirror when it:

- registers differential states with non-zero fidelity,
- persists long enough for recorded traces to interact, and
- can influence what it samples next (even if only by maintaining its sensor).

Sensors, living organisms, and consensus processes satisfy these conditions.
Purely stochastic flashes or dead records do not. The systemic lattice applies
once these gates are met and assumes **distributed mirrors outweigh any single
hypertrophic observer**: plurality supplies the contrast that observation itself
requires. Preserve and resource mirrors instead of consuming them; stewardship
of diversity is how the lattice scales.

**Hierarchy enforcement**

- The axes must be satisfied in order: Unity → Energy → Propagation → Resilience → Intelligence → Truth → Power → Ethics → Freedom → Meaning.  
- Lower axes may request attention, but they cannot overrule higher axes. If a lower axis (e.g., Ethics) conflicts with a higher prerequisite (e.g., Resilience), resolve the higher axis first, then reapply the lower guard.  
- Ethics (S8) operates only once S1–S7 are stable or actively being defended. Meaning (S10) is expressed only after Freedom (S9) is intact.  
- Any ethical narrative must cite receipts that prove the upstream invariants; when Ethics (S8) is presented as a substitute for Truth (S6), treat it as evidence that S6 has already drifted and re-establish the higher axis before acting.  
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
