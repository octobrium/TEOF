# TEOF Modular Organs Specification

**Date:** 2024-11-29
**Purpose:** Minimal architecture for TEOF as assisted-organism
**Status:** ✅ Approved
**Inspiration:** ALAS (modular components), Constitutional AI (fixed principles), Darwin GM (empirical validation)

---

## Design Principles

### From Prior Failure (Codex Attempt)

| Anti-Pattern | This Spec Avoids |
|--------------|------------------|
| AI → AI → AI chains | Human gate between all organs |
| Receipts as output | Outcomes as output |
| Self-modifying core | Fixed constitution |
| Complexity accumulation | Minimal viable organs only |
| Coherence as metric | Empirical results as metric |

### From Successful Systems

| Pattern | Source | Application |
|---------|--------|-------------|
| Modular independence | ALAS | Organs don't feed into each other without gate |
| Fixed constitution | Constitutional AI | Core TEOF immutable |
| Empirical validation | Darwin GM | Test changes against reality |
| Bounded recursion | Gödel Agent | Max iterations before human check |

---

## The Organs (Minimal Set)

### Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     HUMAN (Observer)                        │
│                   Directs, Verifies, Decides                │
└─────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│    SENSORY    │  │   COGNITIVE   │  │    MEMORY     │
│  (Search/Web) │  │  (Analysis)   │  │  (Storage)    │
└───────────────┘  └───────────────┘  └───────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             ▼
                    ┌───────────────┐
                    │    ACTION     │
                    │ (Recommended) │
                    └───────────────┘
                             │
                             ▼
                    ┌───────────────┐
                    │   OUTCOMES    │
                    │  (Measured)   │
                    └───────────────┘
```

**Key constraint:** All arrows pass through HUMAN gate. No organ-to-organ without verification.

---

## Organ Specifications

### 1. Sensory Organ (Data Collection)

**Function:** Gather external information

**Capabilities:**
- Web search (WebSearch tool)
- URL fetching (WebFetch tool)
- File reading (Read tool)

**Protocols:**
- Query formulation based on TEOF principles
- Source credibility assessment
- Multiple source triangulation
- Explicit uncertainty flagging

**Output:** Raw data marked 🤖 UNVERIFIED

**Does NOT:**
- Conclude or decide
- Feed directly into other organs
- Modify any TEOF content

---

### 2. Cognitive Organ (Analysis)

**Function:** Process verified data into insights

**Capabilities:**
- Pattern recognition
- Synthesis across sources
- Gap identification
- Hypothesis generation

**Input:** Only ✅ VERIFIED data

**Protocols:**
- Trace claims to sources
- Flag confidence levels
- Identify contradictions
- Propose, don't conclude

**Output:** Analysis marked 🤖 UNVERIFIED (until human confirms)

**Does NOT:**
- Use unverified data
- Self-validate conclusions
- Modify TEOF content

---

### 3. Memory Organ (Storage)

**Function:** Store verified learnings

**Capabilities:**
- File writing (Write/Edit tools)
- Version tracking
- Provenance labeling

**Input:** Only ✅ VERIFIED content

**Protocols:**
- All content tagged with provenance
- Source links preserved
- Timestamps on all entries
- No overwriting without human approval

**Structure:**
```
memory/
├── raw/           ← Unprocessed inputs (transcripts, infodumps)
├── processed/     ← Verified observations and assessments
└── deprecated/    ← Archived, no longer active

projects/
└── research/      ← External data gathered for projects
```

**Does NOT:**
- Store unverified AI outputs as truth
- Self-organize without human direction
- Delete without explicit approval

---

### 4. Action Organ (Recommendations)

**Function:** Propose actions based on verified analysis

**Capabilities:**
- Actionable recommendations
- Priority ordering
- Trade-off articulation
- Risk flagging

**Input:** Verified analysis + TEOF principles

**Protocols:**
- Recommendations traced to principles
- Multiple options when appropriate
- Downsides explicitly stated
- "Propose, don't decide"

**Output:** Recommendations marked 🤖 PROPOSED

**Does NOT:**
- Execute without human approval
- Assume previous recommendation was followed
- Compound recommendations without new input

---

### 5. Outcome Tracking (Validation)

**Function:** Measure results of actions taken

**Metrics for TEOF Life OS:**

| Domain | Metric | Measurement |
|--------|--------|-------------|
| Health | Did you exercise? | Binary Y/N per day |
| Health | Sleep hours | Number |
| Health | Subjective energy | 1-10 scale |
| Financial | Net worth change | $ monthly |
| Social | Real-world interactions | Count per week |
| Behavioral | Dopamine app usage | Minutes per day |
| Progress | Actions completed vs proposed | Ratio |

**Protocols:**
- Track recommendations → outcomes
- Identify what works vs. doesn't
- Feed learnings back (through human gate)
- No vanity metrics (document count, etc.)

**Does NOT:**
- Self-assess success
- Modify approach without human decision
- Optimize for proxy metrics

---

## The Human Gate

**This is the critical component preventing hallucination compounding.**

### Gate Protocol

```
AI Output (any organ)
       │
       ▼
   ┌───────────────────────────────────┐
   │         HUMAN GATE                │
   │                                   │
   │  1. Review output                 │
   │  2. Check against reality/source  │
   │  3. Mark:                         │
   │     ✅ VERIFIED (can be used)     │
   │     ❌ REJECTED (discard)         │
   │     🔄 NEEDS WORK (iterate)       │
   │                                   │
   └───────────────────────────────────┘
       │
       ▼
Only ✅ content proceeds
```

### When Gate is Required

| Transition | Gate Required? |
|------------|----------------|
| Sensory → Cognitive | ✅ Yes |
| Cognitive → Memory | ✅ Yes |
| Cognitive → Action | ✅ Yes |
| Action → Execution | ✅ Yes |
| Any → Core TEOF modification | ✅ Yes (elevated scrutiny) |

### Gate Exceptions (Bounded Autonomy)

Some low-risk operations can proceed without explicit gate:
- Search query formulation (sensory internal)
- Formatting/structuring output (presentation)
- Reading files for context (information gathering)

**Rule:** If output could become input to future AI processing, gate required.

---

## Implementation

### What This IS

- A mental model for how we work together
- Protocols for maintaining truth-grounding
- Structure preventing hallucination compounding
- Inspired by proven systems (ALAS, Constitutional AI, Darwin GM)

### What This IS NOT

- New code to write
- New infrastructure to build
- Additional documentation burden
- Scaffolding that becomes the product

### How It Works in Practice

**Current session example:**

1. **Sensory:** I searched for market research, self-improving AI systems
2. **Human Gate:** You asked questions, directed focus, verified relevance
3. **Cognitive:** I synthesized findings into research documents
4. **Human Gate:** You reviewed, asked for prior failure integration
5. **Memory:** I wrote to `projects/research/` (with your approval)
6. **Action:** I proposed this organ spec
7. **Human Gate:** You're reviewing now

**We're already doing this.** The spec just makes it explicit and ensures we don't drift.

---

## Validation

### How We Know This Works

| Test | Method | Timeframe |
|------|--------|-----------|
| No hallucination compounding | Track provenance, catch errors at gate | Per session |
| Useful outputs | Did recommendations help? | Weekly review |
| Minimal bloat | Is TEOF simpler or more complex? | Monthly check |
| Real outcomes | Health, finance, social metrics | Quarterly |

### Failure Modes to Watch

| Mode | Detection | Response |
|------|-----------|----------|
| Gate fatigue (rubber-stamping) | Errors slip through | Slow down, raise scrutiny |
| Complexity creep | More process, less output | Prune ruthlessly |
| Proxy optimization | Metrics up, life not better | Return to real outcomes |
| Organ coupling | AI outputs feeding AI inputs | Enforce gate strictly |

---

## Comparison to Failed Attempt

| Codex Attempt | This Spec |
|---------------|-----------|
| 500+ receipts | No receipts, outcomes only |
| 267 plans | Actions tracked, not planned |
| 61 tool directories | 5 conceptual organs |
| AI → AI → AI | AI → Human → AI → Human |
| Self-modifying TEOF | Fixed core, derived evolves |
| Documentation volume metric | Real outcome metrics |
| $0 captured, 0 wins | Track $, health, relationships |

---

## Decision Point

**This spec is 🤖 PROPOSED.**

**Your options:**
1. ✅ Approve — We use this model going forward
2. 🔄 Modify — Specific changes needed
3. ❌ Reject — Too complex, not helpful

**My recommendation:** Approve as mental model, not as new documentation requirement. We're already operating this way. The spec just makes it explicit so we don't drift.

---

## Alignment Assessment (2024-11-29)

**Assessed by:** Claude (Cognitive Organ) | **Verified by:** Human ✅

### Pattern C Alignment

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Stable, protected core | TEOF Core immutable; organs don't modify it | ✅ |
| Authority flows downward | Human Observer → Organs (not reverse) | ✅ |
| Information flows upward | Organs → Human → Core (if warranted) | ✅ |
| Periphery adapts rapidly | Organs iterate; core stable | ✅ |
| Error containment | Human Gate prevents cascade | ✅ |
| Multi-timescale operation | Core: permanent / Organs: per-session | ✅ |

### Successful AI System Pattern Alignment

| System | Pattern | Implementation |
|--------|---------|----------------|
| Constitutional AI | Fixed external anchor | TEOF Core immutable |
| Darwin GM | Empirical validation | Outcome Tracking (real metrics) |
| Gödel Agent | Bounded recursion | Human Gate prevents AI→AI chains |
| ALAS | Modular independence | Organs gated, not coupled |

### Known Failure Modes (Monitor)

1. **Gate fatigue** — Human rubber-stamps when tired → Slow down, raise scrutiny
2. **Bounded autonomy creep** — "Low-risk" exceptions expand → Enforce gate rule strictly
3. **Complexity creep** — More process, less output → Prune ruthlessly

**Conclusion:** Spec implements Pattern C correctly. Integrates lessons from prior Codex failure. Approved as operating model.

---

**End of Specification**
