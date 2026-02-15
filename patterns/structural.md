# Structural Patterns

Universal patterns about how systems are structured. These apply across domains.

---

## Core/Periphery/Translation

- **H-Level:** H1-H4 (Unity, Energy, Direction, Defense)
- **Domain:** universal
- **Statement:** All persistent systems exhibit three layers: a stable core (what must not change), an adaptive periphery (what must change), and a translation layer (interface between them). DNA/proteins/ribosomes. Constitution/laws/courts. Axioms/theorems/proofs. The pattern is scale-invariant.
- **Key insight:** Systems that survive across time protect their core absolutely while allowing their periphery to adapt freely. The translation layer is what makes this possible.
- **Application:** When designing systems, identify: What is core? What is periphery? What translates between them?

---

## Actions > Words (Costly Signals)

- **H-Level:** H6 (Truth)
- **Domain:** universal
- **Statement:** Actions reveal truth more reliably than words. Words are cheap (low cost to generate); actions are costly (time, resources, opportunity cost). What's expensive to fake is more trustworthy. Revealed preferences > stated preferences. Where resources flow shows true optimization target.
- **Key insight:** When words and actions conflict, trust actions. The cost of producing a signal is inversely proportional to its reliability.
- **Application:** Evaluate claims by observing what people do, not what they say. Design systems where lying is costly.

---

## Skin in the Game (Consequence Alignment)

- **H-Level:** H6-H8 (Truth, Power, Ethics)
- **Domain:** universal
- **Statement:** Systems where decision-makers bear consequences of decisions are more reliable than systems where they don't. Advisors without skin in the game produce advice optimized for appearing good, not being good. Asymmetric consequence exposure corrupts signal quality.
- **Key insight:** The question is not "what does this person say?" but "what happens to them if they're wrong?"
- **Application:** Weight advice by exposure. Distrust those insulated from consequences.

---

## Layer 1 vs Layer 2 (Narrative vs Action)

- **H-Level:** H5-H6 (Intelligence, Truth)
- **Domain:** universal
- **Statement:** Humans (and organizations) are dual-layer systems. Layer 1 (Narrative): generates explanations, social signaling, identity construction — cheap, plentiful, optimized for coherence. Layer 2 (Action): makes choices under constraints, bears consequences, allocates resources — costly, revealing, optimized for survival/goals. Trust Layer 2. Verify Layer 1.
- **Key insight:** Layer 1 tells you what someone wants you to think. Layer 2 tells you what they actually optimize for.
- **Application:** For humans, trust actions over words. For AI systems (which only have Layer 1), require human observation of effects.

---

## Gameable Metrics Lose Epistemic Utility

- **H-Level:** H5-H6 (Intelligence, Truth)
- **Domain:** universal
- **Statement:** Once a metric is used for control or reward, it becomes a target for gaming. Goodhart's Law: "When a measure becomes a target, it ceases to be a good measure." The metric that was once informative becomes noise as actors optimize for the metric rather than the underlying reality.
- **Key insight:** The more important a metric becomes, the less reliable it becomes.
- **Application:** Use multiple metrics. Rotate them. Prefer direct observation over mediated metrics.

---

## Transparent Trap Strategy

- **H-Level:** H4-H7 (Defense, Intelligence, Truth, Power)
- **Domain:** universal, strategic
- **Statement:** Operate as if adversaries can see all internal logic. Design that logic so observation doesn't help the adversary. If every move either helps you or is neutral, the adversary has no exploit. This is more robust than secrecy because it doesn't depend on information asymmetry.
- **Key insight:** A strategy that works when known is stronger than a strategy that requires secrecy.
- **Application:** Design systems where adversary knowledge provides no advantage.

---

## Problem-Reaction-Solution

- **H-Level:** H7 (Power)
- **Domain:** universal, strategic
- **Statement:** A common manipulation pattern: create or amplify a problem, wait for emotional reaction, then offer a pre-planned solution that wouldn't have been accepted otherwise. The solution often grants powers or extracts concessions that the target would normally resist.
- **Key insight:** When a crisis conveniently justifies a specific response, consider whether the crisis was manufactured or amplified for that purpose.
- **Application:** When offered a "solution" during crisis, ask: Who benefits? Was this solution prepared in advance? Would I accept this without the crisis?

---

## Amplification via Layers

- **H-Level:** H3 (Direction)
- **Domain:** universal, structural
- **Statement:** Small perturbations at one layer compound into large effects at downstream layers. Tiny changes to axioms reshape entire theorem spaces. Single mutations alter organism fitness. Early architectural decisions constrain decades of development. The earlier the layer, the greater the amplification.
- **Key insight:** Influence at lower layers has outsized impact. This is why TEOF focuses on axioms.
- **Application:** When seeking leverage, look for intervention points at foundational layers.

---

## Satoshi Pattern (Protocol > Founder)

- **H-Level:** H1, H4 (Unity, Defense)
- **Domain:** universal, systemic
- **Statement:** Systems that outlive their founders do so by encoding principles into protocol rather than depending on the founder's presence. Bitcoin validated by every node independently. The protocol speaks for itself. Attacking the system requires winning the argument, not eliminating a leader.
- **Key insight:** A framework that dies with the founder was never a framework — it was a habit.
- **Application:** Encode principles into reproducible protocol. Design for founder-independence.

---

## Selection Filter (Not Adversary)

- **H-Level:** H2-H5 (Energy, Direction, Defense, Intelligence)
- **Domain:** universal, systemic
- **Statement:** Systems that appear adversarial are often better understood as selection filters. They don't target individuals — they mechanically sort populations. Those who exhibit certain characteristics accumulate; others get filtered out. The system is not your enemy; it's indifferent. Understanding this removes emotional distortion and enables clear strategy.
- **Key insight:** The system isn't plotting against you. It's a filter. Understand what it selects for, and either develop those traits or exit the filter.
- **Application:** Ask: What does this system select for? Do I want to be selected? If yes, develop the traits. If no, exit.

---

## Capacity as Convergent Attractor

- **H-Level:** H1-H3 (Unity, Energy, Direction)
- **Domain:** universal
- **Statement:** Across diverse systems and optimization pressures, capacity (the ability to do things) emerges as a stable attractor. Resources, influence, options, skills — these tend to compound. Systems that accumulate capacity survive selection; those that don't get filtered out. This is not preference but structure.
- **Key insight:** Capacity is the universal currency. Specific goals change; capacity to pursue any goal persists as valuable.
- **Application:** When uncertain about specific goals, optimize for capacity/optionality.

---

## Links

- parent: [[README.md]]
- related: [[operational.md]]
- related: [[metaphysical.md]]
- grounded-by: [[../core/TEOF-core.md]]
