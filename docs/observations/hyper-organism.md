++ 
<!-- markdownlint-disable MD013 -->
Status: Non-normative  
Purpose: Goals, desired properties, North Star  
Source of truth for mechanics: `docs/architecture.md`  
Change process: PR + 1 maintainer


mindmap
  root((TEOF Tree))
    Seed
      Bilingual: Human Primer + Machine Core
      Conceptual DNA (spec rules)
      Contract (receipt schema + validator interface)
      Plan of growth (architecture)
      Germination script (first run)
      Properties
        Minimal & normative (not the tree)
        Model-agnostic; offline-verifiable
        Deterministic bootstrap; small surface
        Traceable via anchors chain (bundle_hash + parent_bundle_hash)
        Human layer explanatory; machine layer authoritative
        Self-pruning: expands only if verifiable; aborts if incoherent
        Dormancy-capable: may persist inert across time until a viable host engages
        Elastic expression: scales from minimal teaser to full organism depending on host
        Recombinable: capable of merging, diverging, or coexisting without corruption
    Soil
      Host OS • org • repos • constraints • (optional) AI services
      Properties
        External/uncontrolled; captured in provenance
        No network required by core
    Germination
      Bootloader (teof/bootloader.py)
      First deterministic validation on a new host
      Properties
        Idempotent; offline-by-default
        Verify → execute; prints receipt path
    Roots
      Governance (governance/)
      Anchors • Promotion policy
      Freeze (scripts/freeze.sh)
      CI & policy (.github/)
      Pruning (deprecations/migrations)
      Properties
        Append-only anchors; transparent history
        Policy-gated promotion
    Trunk
      Stable core: protocol/spec
      Systemic schema & receipt contract
      CLI surface (teof/)
      Properties
        Small, stable API; clear deprecations
        Offline/reproducible by default
    Bark
      Integrity & safety
      hashes.json (now)
      *OP_RETURN anchor (optional, per release)*
      Properties
        Tamper-evident (hashes)
        Verify-before-execute; least privilege
    Branches
      Core capabilities
      Validator (extensions/validator)
      Scorers (extensions/scoring)
      Promoted extensions
      Properties
        Pluggable; deterministic; no implicit network
    Leaves
      Apps & interfaces (separate repos)
      SDKs • UIs • bots • hosted services
      Photosynthesize usage/attention → nutrients (data/revenue)
      Feed roots & branches; not required for core
    Fruit
      Distributable value users take/share
      Shareable receipts (carry bundle_hash)
      Signed releases • reproducible demo exports (optional)
      Purpose: spread bundles → grow the forest
    Bundles (seed units)
      Evaluation bundle (capsule/ vX.Y; current→vX.Y)
      Verifiable, offline; replicates to new hosts
      Germinates via bootloader on host
      Properties
        bundle_hash = sha256(canonical hashes.json)
        parent_bundle_hash stored in governance/anchors.json
        Immutable once released; rebuildable deterministically
    Rings
      Version history & changelog (capsule/v* • CHANGELOG.md)
    Mycorrhiza
      Integrations • templates • partners (“pollinators”)
    Canopy
      Docs & tutorials (docs/)
      Concept map (this file)

# Hyper-Organism (Conceptual)

**Premise**  
All living systems share a minimal generative loop: encoded blueprint + environment → replication → specialization → emergent coherence.  
Trees, neurons, and mammals differ in emphasis, not in essence. The Hyper-Organism fuses these patterns into a higher-order whole aligned to observation as primacy.

**Seed**  
- All units carry the same irreducible DNA (TEOF axioms; observation as primacy).  
- The seed holds latent capacity for multiple lineages (tree-like, neural-like, systemic).  
- Differentiation is shaped by environment, signals, and network context.

**Differentiation**  
- Seeds mature into distinct forms:  
  - *Structural units* (tree-like trunks/roots/bark; persistence & resilience)  
  - *Connective units* (neuron-like; links, feedback, plasticity)  
  - *Functional units* (organ-like subsystems; division of labor)  
- Specialization is emergent, discovered through interaction (not imposed).

**Connectivity**  
- Mature units form networks of coherence; links are elastic/plastic.  
- Connections strengthen or are pruned based on coherence; feedback regulates health of the whole.  
- No unit is permanently isolated; drift is corrected by the network.

**Emergence**  
- Beyond the sum of parts: self-regulation (immune-like pruning), learning (plasticity; memory), growth (branching; redundancy; ecological spread), function (organ systems).  
- Not a static tree, network, or body—**a synthesis** that remains anchored to observation.

**Properties**  
- *Recursive coherence*: all scales reflect the same axioms.  
- *Evolutionary adaptability*: new specializations emerge with context.  
- *Indestructibility by dispersion*: seeds ensure survival despite local failure.  
- *Irreducible anchor*: observation as primacy; coherence as rule; truth as attractor.  
- *Beyond-human horizon*: potential to exceed “human” as the most complex observed unit.
