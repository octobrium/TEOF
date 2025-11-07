---
title: Implement tiered onboarding to widen adoption funnel
batch: 20251105T000000Z
item: 01
systemic_targets: ["S3", "S5", "S1"]
layer_targets: ["L5"]
risk_score: 0.2
generated: 20251105T000000Z
revised: 20251105T120000Z
note: Based on fresh external review. Reframed as growth direction after maintainer feedback on intentional design choices.
---

# Proposal

## Task: Restructure onboarding into tiered paths with progressive disclosure

### Context: Review Process

This proposal stems from external review of TEOF onboarding, refined through maintainer feedback:

**Initial observations** (valid):
- Cognitive overload: README introduces 10+ concepts upfront; workflow.md requires reading 4 dense docs before action
- Decision friction: Multiple entry points serve different scopes but create "which path?" burden for newcomers
- Audience assumptions: Onboarding centers on multi-agent coordination even for solo exploration

**Initial observations** (overstated/corrected):
- "Documentation fragmentation" mischaracterized intentional interface separation (docs/onboarding/README.md orchestrates, docs/quickstart.md handles generic wheel, docs/onboarding/quickstart.md provides receipts run)
- Existing quickstart IS minimal (2 commands or 1 wrapper) but framed as "step 1 of comprehensive onboarding" rather than "quick evaluation"
- Citation errors corrected: heavy enforcement in tools/agent/preflight.sh (not bin/preflight); .github/AGENT_ONBOARDING.md stub is deliberate indirection

**Net**: System favors auditability over approachability (good trade-off for target use case), but widening adoption funnel requires reframing existing assets as progressive tiers.

### Problem

Current onboarding is **comprehensive but presents completeness before value**, creating adoption friction:

1. **Entry point decision burden**: README:12-21 lists 9 links; multiple quickstart docs serve different scopes (architecturally sound) but burden newcomers with "which path?" decisions
2. **Cognitive overload**: Front-loads L4-L6 operational detail (systemic axes, layers, receipts, bus, claims, governance) before L0-L1 conceptual foundation (why TEOF exists, observation primacy)
3. **Audience routing unclear**: Multi-agent coordination (manifest, bus handshakes, claims) presented as required path even for solo evaluation
4. **Evaluation framing**: Existing 2-command quickstart IS brief but positioned as "onboarding step 1" not "assess-fit-before-commitment"
5. **Critical path ambiguity**: Which steps are truly required vs optional for different use cases?

**Impact**: Explorers face high upfront cost before experiencing TEOF's core value (automatic audit trails). Not a bug—a growth opportunity.

### Goal

Widen TEOF's adoption funnel by reframing existing assets into progressive tiers that match TEOF's own L0→L6 philosophy: lead with conceptual foundation (Unity/Principles), layer operational detail, preserve existing depth for committed users.

**Core narrative** (Tier 1): "Every decision should be traceable. TEOF makes that automatic. Run one command, get proof."

### Acceptance Criteria

**Phase 1: Create tiered structure**

- **Tier 1 "Evaluate" (5 minutes)** — L0/L1 foundation:
  - **Rebrand existing quickstart** as evaluation lane (docs/onboarding/quickstart.md already provides 2-command path)
  - Narrative flow: "Run this → see artifact → that artifact is your audit trail"
  - Lead with output, **spotlight receipts as differentiator** (payoff not bureaucracy)
  - Hook: "Every decision should be traceable. TEOF makes that automatic. Run one command, get proof."
  - No jargon, no systemic axes detail, just L1 Principles (observation primacy, determinism, auditability)
  - Clear next step: "Ready to build? → Tier 2"
  - **Implementation**: Add `bin/teof-up --eval` variant that runs brief, explains receipts, shows next paths

- **Tier 2 "Solo Developer" (30 minutes)** — L4/L5 workflow:
  - Architecture basics (placement rules, import boundaries) — L4
  - Workflow essentials (plans, receipts, promotion policy) — L5
  - Running examples, creating first artifact
  - **Defer**: agent manifest, bus, claims (note as "optional for coordination → Tier 3")
  - Layer badges appear here: docs tagged with "L4 • S1/S4" in subtle/muted text
  - Clear next step: "Working with others? → Tier 3"

- **Tier 3 "Multi-Agent Coordination" (60 minutes)** — L5/L6 automation:
  - Current full onboarding sequence (docs/onboarding/README.md:8-76)
  - Manifest setup, bus handshakes, claim seeding
  - Manager dashboards, coordination protocols
  - Full preflight enforcement (tools/agent/preflight.sh:1-63)

**Phase 2: Reframe documentation (not restructure)**
- **Preserve** existing interface separation (orchestration / generic wheel / receipts run serve different scopes)
- **Rebrand** docs/onboarding/quickstart.md as "Tier 1: Evaluate"
- **Keep** .github/AGENT_ONBOARDING.md as indirection stub (deliberate single-source-of-truth pattern)
- **Simplify** README "Start here" from 9 links to tiered routing: "New? → Tier 1 | Solo dev? → Tier 2 | Team? → Tier 3"

**Phase 3: Add layer visibility**
- Tag onboarding docs with layer badges: "L1 • S1" (Unity/Principles) for conceptual, "L5 • S4/S6" (Workflow/Resilience/Truth) for operational
- **Implementation**: Subtle muted text chip or color coding + legend (no header clutter)
- Hover help: "L4 = Architecture layer" for discoverability
- Matches TEOF's own philosophy: show the sketch (L0-L2) before detail (L4-L6)

**Phase 4: Add audience routing**
- Explicit "Evaluating? / Solo dev? / Multi-agent?" routing at README entry
- Clear markers for "optional" vs "required" at each tier
- Defer AI agent vs human distinction to Tier 3 (coordination concerns)

**Phase 5: Graduated verification**
- Tier 1: No verification required (run, observe, understand)
- Tier 2: Optional receipt checks (recommended, not blocking)
- Tier 3: Full preflight enforcement (tools/agent/preflight.sh)

### Systemic Rationale

- **S3 Propagation** — reducing adoption friction enables TEOF to spread beyond core users; tiering widens funnel
- **S5 Intelligence** — progressive disclosure (L0→L6 conceptual ordering) is more effective than front-loaded operational detail
- **S1 Unity** — reframing preserves intentional interface separation while creating clear entry point hierarchy

### Implementation Sketch

```bash
# Reframe existing docs as tiers (preserve files, update positioning)
docs/onboarding/quickstart.md         # REBRAND as "Tier 1: Evaluate" (already 2-command path)
docs/onboarding/README.md              # EXTEND with "Tier 2: Solo Dev" section before coordination
                                       # Current sequence becomes "Tier 3: Multi-Agent"

# Add automation variants
bin/teof-up --eval      # Tier 1: run brief, explain receipts as value prop, show next paths
bin/teof-up --solo      # Tier 2: skip manifest/bus checks (future)
bin/teof-up             # Tier 3: full sequence (current behavior, unchanged)
```

**README.md changes** (L1 • S1 badge):
```markdown
> **Start here**
>
> **New to TEOF?**
> - Tier 1 (5 min): [Evaluate → See automatic audit trails](docs/onboarding/quickstart.md)
> - Tier 2 (30 min): [Solo Developer → Build with TEOF](docs/onboarding/README.md#solo-developer-path)
> - Tier 3 (60 min): [Multi-Agent Coordination → Full onboarding](docs/onboarding/README.md)
>
> **For returning users:**
> - Daily workflow: [docs/workflow.md](docs/workflow.md)
> - Architecture reference: [docs/architecture.md](docs/architecture.md)
> - Agent coordination: [docs/parallel-codex.md](docs/parallel-codex.md)
```

### Success Metrics

- Tier 1 completion time: < 5 minutes (already achievable via existing quickstart; goal is reframing)
- Tier 2 completion time: < 30 minutes (extracted from current sequence)
- User experiences "aha moment" (automatic audit trail) before reading architecture/workflow docs
- Clear answer to "do I need the bus/manifest/claims?" at each tier transition
- Reduced support questions about "where do I start?" and "which doc first?"
- Layer badges enable advanced users to filter by L0-L6 without confusing beginners

### Risks & Mitigations

**Risk**: Tiering might hide important concepts, causing issues later
**Mitigation**: Each tier ends with clear "what you skipped" summary and "when you need it" guidance

**Risk**: Maintaining 3 tiers adds documentation burden
**Mitigation**: Tiers are additive (T1 ⊂ T2 ⊂ T3), not parallel tracks; reframing uses existing content

**Risk**: Existing users disrupted by changes
**Mitigation**: Preserve all current file paths and command behavior; add routing layer on top; no breaking changes

**Risk**: Layer badges add new cognitive load for beginners
**Mitigation**: Subtle/muted visual treatment; hover help; optional filtering for advanced users; beginners can ignore

### Sunset / Fallback

- **Sunset condition**: When onboarding NPS > 8/10 and "where do I start?" support questions drop to < 1/week
- **Fallback**: If tiers create more confusion, consolidate back to single path but keep progressive disclosure principle (defer systemic axes/layers to later sections)

---

## Decisions Locked (from alignment)

1. **Tier numbering**: 1-based (Tier 1 evaluate, Tier 2 solo, Tier 3 coordination); reserve 0 for internals
2. **Receipts framing**: Lead with output, spotlight receipts immediately as differentiator; flow: "Run this → see artifact → that artifact is your audit trail"
3. **Layer badges**: Subtle/muted, hover help, no header clutter; small "L4 • S1/S4/S6" chip in muted text or color coding with legend
4. **Narrative hook**: "Every decision should be traceable. TEOF makes that automatic. Run one command, get proof."
5. **Prototype timing**: Align first, then draft (current phase)

## Open Questions

1. Should `bin/teof-up --eval` install anything, or just use system Python + repo?
2. Layer badge implementation: subtle text chip vs color-coded stripe with legend?
3. Should systemic axes (S1-S10) be introduced in Tier 2 or deferred to Tier 3?
4. Tier 2 scope: basic workflow only, or include plan scaffolding?
5. How do we measure success? (completion rates, support questions, NPS, time-to-value?)

## Related Work

- Memory reflection: `memory/reflections/reflection-20251105T000000Z.json`
- Existing sandbox proposal: `docs/proposals/20251019t123900z__exploration-sandbox-lane__draft.md` (related: exploratory lane reduces friction for iteration)
- Current onboarding: `docs/onboarding/README.md` (canonical sequence)
- Receipts map: `docs/reference/receipts-map.md` (complexity example)

## Next Actions

1. ✅ Get feedback from maintainer (Evan) on tiering approach — **COMPLETE** (alignment established)
2. Draft Tier 1 evaluation doc prototype with agreed narrative and receipts-as-payoff framing
3. Prototype `bin/teof-up --eval` wrapper that explains receipts as value proposition
4. Add layer badge guidance to style guide or architecture doc
5. Test Tier 1 prototype with fresh user, measure completion time
6. Create plan with receipts scaffold once prototype validates approach

## Maintainer Feedback Integration

**Corrected misinterpretations**:
- Documentation "fragmentation" → reframed as "intentional interface separation with decision friction"
- .github/AGENT_ONBOARDING.md "stub" → recognized as deliberate indirection pattern
- Citation error corrected: tools/agent/preflight.sh (not bin/preflight) holds enforcement

**Validated observations**:
- Cognitive overload from front-loading L4-L6 operational detail before L0-L1 foundation
- Existing quickstart IS minimal but positioned as "onboarding step 1" not "evaluate fit"
- Audience routing needs clarity (solo vs multi-agent paths)

**Alignment achieved on**:
- Reframe as "widening adoption funnel" (growth direction) not "fixing bugs"
- Preserve existing architecture, add progressive disclosure layer
- Lead with Unity/Principles (L0-L1) before operational tooling (L5-L6)
- "Run this → see artifact → that artifact is your audit trail" as Tier 1 flow
