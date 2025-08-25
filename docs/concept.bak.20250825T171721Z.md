Status: Non-normative
Purpose: Goals, desired properties, North Star
Source of truth for mechanics: Architecture.md
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
      OCERS schema & receipt contract
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
      Feed roots & branches; never required for core
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
