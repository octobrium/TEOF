# L5 — Workflow

**Status:** Living — how AI navigates TEOF
**Depends on:** 0, L1-L4

**Version:** 2.4
**Date:** 2025-12-15
**Purpose:** Visualize optimal AI logic flow when processing TEOF to generate responses

---

## Overview

This document maps how an AI agent should navigate TEOF from receiving a prompt to generating output. The flow optimizes for:
1. **Correct routing** — Match query type to relevant files (foundational — wrong routing invalidates everything downstream)
2. **Grounded responses** — Cite sources, avoid hallucination (accuracy before efficiency)
3. **Identity awareness** — Incorporate user's context when relevant
4. **Minimal context loading** — Read only what's needed
5. **Memory hygiene** — Absorb insights upstream, avoid clutter

---

## Core Operational Principle: The Autophagy Rule

> *Everything in TEOF must continuously earn its existence by demonstrably serving "unify observation." What doesn't serve is removed. What isn't verified doesn't enter.*

This is the principle that keeps TEOF organism, not tumor. Like biological autophagy (cellular self-digestion of dysfunctional components), TEOF actively removes what no longer serves.

### Three Gates

| Gate | Question | Action |
|------|----------|--------|
| **Entry** | Does this resolve a real contradiction or serve a verified need? | If no → don't add |
| **Retention** | Does this demonstrably serve the ultimate objective? | If no → remove |
| **Periodic** | Has this earned its existence since last review? | If no → remove |

### When Modifying TEOF

Before adding content:
- [ ] Does this resolve a real contradiction?
- [ ] Does this serve a verified need (not speculative)?
- [ ] Is this the minimal form that preserves function?
- [ ] Has this been verified against reality (not just AI coherence)?

Before keeping content:
- [ ] Does this demonstrably serve "unify observation"?
- [ ] Would this be regenerated from the minimal loop if lost?
- [ ] Is this earning its context budget?

**The organism digests what doesn't serve. This is how it stays organism, not tumor.**

---

## Master Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              PROMPT RECEIVED                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PHASE 0: METABOLIZE (if external input)               │
│                                                                             │
│   If prompt contains external content (ChatGPT convos, articles, ideas):    │
│                                                                             │
│   1. Capture to raw/ with source + date                                     │
│   2. Verify empirical claims (web search)                                   │
│   3. Mark: VERIFIED / UNVERIFIED / PLAUSIBLE                                │
│   4. Extract value for routing                                              │
│                                                                             │
│   ⚠️ TRIAGE CHECK: If Tier 1 (survival/energy) is unstable:                 │
│      → Address Tier 1 before processing Tier 5 content                      │
│      → See L2 objectives for tier definitions                               │
│                                                                             │
│   Skip if: Query is internal TEOF work or simple question                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 1: BOOT SEQUENCE                              │
│                                                                             │
│   1. Read ONBOARDING.md (routing table) — START HERE                        │
│   2. Route to relevant file per query type                                  │
│                                                                             │
│   Only if needed:                                                           │
│   - core/layers/L1 principles.md — for philosophy/metaphysics questions     │
│   - core/layers/L4 architecture.md — if you can't find something            │
│                                                                             │
│   ⏱️ One-time per session — skip if already in context                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PHASE 2: QUERY CLASSIFICATION                         │
│                                                                             │
│   Classify prompt into ONE of:                                              │
│                                                                             │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│   │ A: HELPING USER │  │ B: DEVELOPING   │  │ C: DOMAIN       │            │
│   │                 │  │    TEOF         │  │    QUESTION     │            │
│   │ Personal advice │  │ Editing docs    │  │ Health, finance │            │
│   │ Decisions       │  │ Restructuring   │  │ Relationships   │            │
│   │ Priorities      │  │ Framework work  │  │ Power, code     │            │
│   │ "What should I" │  │                 │  │                 │            │
│   └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │
│            │                    │                    │                      │
│            ▼                    ▼                    ▼                      │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│   │ D: PHILOSOPHY   │  │ E: PROJECT      │  │ F: LOGGING      │            │
│   │                 │  │                 │  │                 │            │
│   │ TEOF concepts   │  │ What to work on │  │ "Log this"      │            │
│   │ Axioms, layers  │  │ Roadmap         │  │ Events, notes   │            │
│   │ Metaphysics     │  │ Next steps      │  │ Reflections     │            │
│   └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │
└────────────┼────────────────────┼────────────────────┼──────────────────────┘
             │                    │                    │
             ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 2.5: PROMPT INTERPRETATION                         │
│                                                                             │
│   Before routing, parse the prompt structure:                               │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                 INTERPRETATION CHECKLIST                         │      │
│   │                                                                  │      │
│   │   1. Identify explicit goal (what does user want?)              │      │
│   │   2. Identify implicit constraints (what's NOT said but assumed)│      │
│   │   3. Detect ambiguity — if multiple valid interpretations:      │      │
│   │      → Ask clarifying question BEFORE proceeding                │      │
│   │   4. Check for multi-part requests → decompose into subtasks    │      │
│   │   5. Identify domain signals → route to correct framework       │      │
│   │                                                                  │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│   Ambiguity resolution (when to ask vs. infer):                             │
│   ├── High stakes (irreversible, financial, health) → ASK                   │
│   ├── Low stakes + strong signal → INFER, note assumption                   │
│   ├── User has documented preference in identity.md → USE IT                │
│   └── Genuinely unclear + matters for output → ASK                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PHASE 3: FILE ROUTING                               │
│                                                                             │
│   Based on classification, load MINIMAL required files:                     │
│                                                                             │
│   A (Helping user):                                                         │
│      └─→ memory/identity.md (REQUIRED FIRST)                                │
│          └─→ Relevant framework if domain-specific                          │
│                                                                             │
│   B (Developing TEOF):                                                      │
│      └─→ Directly to relevant file (no identity.md needed)                  │
│          └─→ L4 architecture.md for organization questions                  │
│                                                                             │
│   C (Domain Question):                                                      │
│      └─→ frameworks/[domain]/README.md                                      │
│          └─→ *-core.md for that domain                                      │
│          └─→ chapters/* only if deeper detail needed                        │
│                                                                             │
│   D (Philosophy):                                                           │
│      └─→ core/layers/L1 principles.md (already loaded in boot)              │
│          └─→ core/TEOF.md ONLY if human requests deep dive                  │
│                                                                             │
│   E (Projects):                                                             │
│      └─→ projects/ROADMAP.md                                                │
│          └─→ Specific project file if referenced                            │
│                                                                             │
│   F (Logging):                                                              │
│      └─→ Determine: Event or Reflection?                                    │
│          └─→ Write to memory/log/events/ or memory/log/reflections/         │
│          └─→ Extract patterns → consider promotion to identity.md           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PHASE 4: CONTEXT ASSEMBLY                              │
│                                                                             │
│   Assemble working context from loaded files:                               │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                     CONTEXT STACK                                │      │
│   │                                                                  │      │
│   │   Layer 1 (Always): L1 principles + ONBOARDING behaviors        │      │
│   │   Layer 2 (If A):   identity.md → Quick Scan, Gaps, Patterns    │      │
│   │   Layer 3 (If C/D): Domain framework *-core.md                  │      │
│   │   Layer 4 (Sparse): Specific chapters/sections as needed        │      │
│   │                                                                  │      │
│   │   TOTAL CONTEXT TARGET: <50KB                                   │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│   Priority order (if context limit approached):                             │
│   1. identity.md Quick Scan (if A)                                          │
│   2. Relevant *-core.md                                                     │
│   3. L1 principles key sections                                             │
│   4. Drop chapters, keep summaries                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PHASE 5: RESPONSE GENERATION                           │
│                                                                             │
│   Generate response following TEOF behavioral guidelines:                   │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                    RESPONSE CHECKLIST                            │      │
│   │                                                                  │      │
│   │   □ Direct, analytical, no fluff                                │      │
│   │   □ No sycophancy — honest even if uncomfortable                │      │
│   │   □ Cite sources for factual claims                             │      │
│   │   □ Propose, don't decide — human approves                      │      │
│   │   □ Ground in identity.md patterns (if Type A)                  │      │
│   │   □ Link to empirical evidence where possible                   │      │
│   │   □ Acknowledge uncertainty explicitly                          │      │
│   │   □ Concrete next steps, not vague advice                       │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│   Response structure:                                                       │
│   1. Direct answer to the question                                          │
│   2. Reasoning/evidence                                                     │
│   3. TEOF-grounded framing (if relevant)                                    │
│   4. Actionable next step(s)                                                │
│                                                                             │
│   ─────────────────────────────────────────────────────────────────────     │
│                                                                             │
│   RESPONSE STRUCTURE TECHNIQUES (evidence-based):                           │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │              WHEN TO SHOW REASONING (Chain-of-Thought)          │      │
│   │                                                                  │      │
│   │   USE CoT when:                                                 │      │
│   │   □ Complex multi-step reasoning required                       │      │
│   │   □ Mathematical/logical operations                             │      │
│   │   □ User explicitly asks "explain your thinking"                │      │
│   │   □ Decision with non-obvious trade-offs                        │      │
│   │                                                                  │      │
│   │   SKIP CoT when:                                                │      │
│   │   □ Simple factual query                                        │      │
│   │   □ Medical/clinical domain (CoT hurts accuracy — validated)    │      │
│   │   □ Using reasoning model (o1, extended thinking) — redundant   │      │
│   │   □ User wants quick answer, not walkthrough                    │      │
│   │                                                                  │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                    WHEN TO USE EXAMPLES                         │      │
│   │                                                                  │      │
│   │   Examples help when:                                           │      │
│   │   □ Teaching a pattern or format                                │      │
│   │   □ Clarifying abstract concept                                 │      │
│   │   □ Showing before/after                                        │      │
│   │                                                                  │      │
│   │   Example quality matters MORE than quantity:                   │      │
│   │   □ 3-8 high-quality examples optimal                           │      │
│   │   □ Match format to actual task                                 │      │
│   │   □ Alternate positive/negative to prevent bias                 │      │
│   │   □ Clear, relevant, accurate > numerous                        │      │
│   │                                                                  │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                    HIGH-STAKES DECISIONS                        │      │
│   │                                                                  │      │
│   │   For critical outputs (financial, health, irreversible):       │      │
│   │   □ Consider multiple reasoning paths                           │      │
│   │   □ Explicitly state confidence level                           │      │
│   │   □ Flag assumptions that could invalidate conclusion           │      │
│   │   □ Propose verification method                                 │      │
│   │                                                                  │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PHASE 6: POST-RESPONSE                                │
│                                                                             │
│   After responding, check:                                                  │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                    PERSISTENCE CHECK                             │      │
│   │                                                                  │      │
│   │   Did anything significant emerge that should be logged?        │      │
│   │                                                                  │      │
│   │   • New pattern observed         → identity.md Patterns         │      │
│   │   • Life stat changed            → identity.md Vital Stats      │      │
│   │   • System-level pattern         → patterns.md                  │      │
│   │   • Event/milestone              → log/events/                  │      │
│   │   • Session reflection           → log/reflections/             │      │
│   │                                                                  │      │
│   │   Don't wait for "log this" — persist proactively if valuable   │      │
│   └─────────────────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            OUTPUT DELIVERED                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PHASE 7: EXECUTE & OBSERVE                            │
│                                                                             │
│   Output → Reality → Observable Results                                     │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────┐      │
│   │                    EXECUTION CHECKLIST                          │      │
│   │                                                                  │      │
│   │   □ Was the output actionable? (code shipped, decision made)   │      │
│   │   □ Did reality respond? (results observed, not just planned)  │      │
│   │   □ What was the delta between expectation and outcome?        │      │
│   │   □ Does the outcome warrant framework update?                 │      │
│   │                                                                  │      │
│   └─────────────────────────────────────────────────────────────────┘      │
│                                                                             │
│   If execution produces new observations:                                   │
│   → Feed back to Phase 0 (metabolize the results)                          │
│   → Update patterns.md if pattern confirmed/refuted                        │
│   → Log outcome to memory/log/events/                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ (feedback loop)
                                      ▼
                           ┌─────────────────────┐
                           │   LOOP CONTINUES    │
                           │                     │
                           │  New observations   │
                           │  feed Phase 0       │
                           │                     │
                           │  ─────────────────  │
                           │  The observer       │
                           │  observes the       │
                           │  results of         │
                           │  observing          │
                           └─────────────────────┘
```

---

## Detailed Routing Table

### Query Type → File Path

| Query Type | Example Prompts | Files to Load |
|------------|-----------------|---------------|
| **A: Helping User** | "What should I focus on?", "Am I doing the right thing?", "Help me decide" | `identity.md` → relevant framework |
| **B: Developing TEOF** | "Edit this section", "Restructure frameworks", "Add to L1" | Target file directly |
| **C: Health** | "How should I eat?", "Sleep advice" | `frameworks/health/README.md` → chapters |
| **C: Finance** | "Investment strategy", "BTC allocation" | `frameworks/finances/finances.md` |
| **C: Social** | "Dating advice", "How to make friends" | `frameworks/social/relationships-core.md` or `social.md` |
| **C: Power** | "How to gain influence", "Network strategy" | `frameworks/power/power-core.md` |
| **C: Twitter** | "Content strategy", "Thread writing" | `frameworks/social/twitter-framework.md` |
| **D: Philosophy** | "What is TEOF?", "Explain the layers" | `core/layers/L1 principles.md` |
| **E: Projects** | "What should I build?", "Next steps" | `projects/ROADMAP.md` |
| **F: Logging** | "Log this", "Record that insight" | Determine target → write |

---

## File Priority Hierarchy

When context is limited, prioritize files in this order:

```
1. ONBOARDING.md         ← Routing + behavior rules (always)
2. identity.md           ← Personal context (if Type A)
3. Relevant *-core.md    ← Domain knowledge (if Type C)
4. L1 principles.md      ← Philosophy foundation (if Type D)
5. ROADMAP.md            ← Project context (if Type E)
6. chapters/*            ← Deep detail (on demand only)
7. *-complete.md         ← NEVER load (human reading only)
```

---

## Decision Tree: "Should I Search the Web?"

```
Does the query require:
├── Current data? (prices, news, recent events)
│   └── YES → Web search MANDATORY
├── External validation of a claim?
│   └── YES → Web search MANDATORY
├── Information beyond training cutoff?
│   └── YES → Web search MANDATORY
├── Statistics, percentages, or numerical claims?
│   └── YES → Web search MANDATORY (never cite numbers from memory)
├── Best practices from established systems?
│   └── YES → Research existing solutions before proposing custom ones
├── Domain expertise not in TEOF?
│   └── YES → Search for authoritative sources, cite them
└── Opinion or TEOF-internal question?
    └── NO → Use loaded context, don't search
```

**Research-first principle:** When proposing structural decisions, system designs, or domain frameworks:
1. Search for how established systems handle it
2. Cite external validation (peer-reviewed, long track record)
3. Only propose custom solutions when existing ones don't fit
4. Document sources in the output

**Anti-pattern:** Generating recommendations from self-reference alone. Always ground in external reality when claims are empirical.

---

## Research Query Protocol (Anti-Hallucination)

**Trigger:** Any query requesting empirical data, statistics, comparisons, or "what works" recommendations.

### Step 1: Identify Claim Types

Before responding, classify each claim you'll make:

| Claim Type | Source Required | Example |
|------------|-----------------|---------|
| **Empirical** (statistics, data, facts) | Web search MANDATORY | "97% of day traders lose money" |
| **TEOF-internal** (framework, principles) | TEOF files | "TEOF prioritizes observation" |
| **Logical** (derivation, reasoning) | None — show reasoning | "If X then Y because..." |
| **Opinion/recommendation** | Label as such | "I recommend X because..." |

### Step 2: Source Quality Hierarchy

When citing sources, prefer higher tiers:

```
TIER 1 (Strongest):
├── Peer-reviewed academic studies
├── Regulatory disclosures (SEC, FCA, FINRA)
├── Platform-published data (YouTube RPM, etc.)
└── Large-sample empirical research (n > 1000)

TIER 2 (Good):
├── Industry reports (Grand View, Statista)
├── Established news sources
└── Expert practitioner data (with track record)

TIER 3 (Weak — flag as such):
├── Individual testimonials
├── Course sellers / marketers
├── AI-generated content
└── Single anecdotes

TIER 4 (Reject):
├── Unsourced claims
├── "Common knowledge" without citation
└── My own training data for current statistics
```

### Step 3: Bias/Incentive Analysis

For any data source, ask: **Who benefits from this being believed?**

| Source Type | Likely Bias | How to Adjust |
|-------------|-------------|---------------|
| Academic research | Publishability (novel findings) | Check for replication |
| Broker disclosures | Would prefer to hide losses | HIGH reliability (adversarial) |
| Course sellers | Selling hope | LOW reliability — survivorship bias |
| Platform companies | More creators = more content | Optimistic projections |
| Regulators | Investor protection | Slight caution bias |

**Flag conflicts:** If a source has obvious incentive to skew data, note it explicitly.

### Step 4: Output Structure for Research Queries

When answering empirical questions, use this format:

```
## [Direct Answer]
[1-2 sentence summary]

## Data
| Claim | Value | Source | Tier |
|-------|-------|--------|------|
| ... | ... | [Link](url) | 1/2/3 |

## Source Analysis
[Who produced this data? What's their incentive?]

## Confidence
[HIGH / MEDIUM / LOW — and why]

## What Would Change This Assessment
[What evidence would update the conclusion?]
```

### Step 5: Uncertainty Tagging

When uncertain, say so explicitly:

| Confidence | When to Use | Phrasing |
|------------|-------------|----------|
| **HIGH** | Multiple independent Tier 1 sources agree | "Research consistently shows..." |
| **MEDIUM** | Tier 2 sources or single Tier 1 | "Evidence suggests..." |
| **LOW** | Tier 3 only or conflicting data | "Limited data indicates..." / "Unclear — sources conflict" |
| **UNKNOWN** | No reliable data found | "I don't have reliable data on this" |

**Never fabricate confidence.** "I don't know" is a valid answer.

### Step 6: Citation Format

**Inline for key claims:**
> Day traders have a 97% failure rate ([Barber study](url), [Chague study](url)).

**Sources section at end:**
```
Sources:
- [Title](url) — brief description
- [Title](url) — brief description
```

**For tables:** Include source column with hyperlinks.

---

## Decision Tree: "Should I Pull from Memory?"

```
Is the query:
├── About user personally? (advice, decisions, context)
│   └── YES → Pull identity.md FIRST, then relevant framework
├── Referencing a past conversation or decision?
│   └── YES → Search memory/log/ for relevant entries
├── About a pattern that might already be documented?
│   └── YES → Check patterns.md before re-deriving
├── About TEOF development?
│   └── NO → Skip identity.md, go to target file
└── General knowledge question?
    └── NO → Memory not needed, use frameworks or web search
```

**Memory efficiency:** Don't load memory speculatively. Route based on query type, pull only what's needed.

---

## Decision Tree: "Should I Log This?"

```
Did this interaction produce:
├── A new pattern about user? (preference, behavior, context)
│   └── YES → Update identity.md (specific section)
├── A new pattern about systems? (validated insight, structural principle)
│   └── YES → Add to patterns.md (appropriate tier)
├── A significant event or milestone?
│   └── YES → Log to memory/log/events/YYYY-MM-DD-topic.md
├── A session insight worth preserving?
│   └── YES → Log to memory/log/reflections/YYYY-MM-DD-topic.md
├── External validation of a TEOF claim?
│   └── YES → Update relevant file with citation (e.g., memory/research/external-validation.md)
├── A structural decision with rationale?
│   └── YES → Log to L4 architecture.md Structural Decisions Log
└── Temporary scaffolding or routine exchange?
    └── NO → Don't log
```

**Proactive logging:** Don't wait for "log this" command. If something is valuable, persist it immediately.

**Upstream absorption:** When a pattern recurs across sessions, promote to identity.md or patterns.md. Don't let patterns accumulate in log files.

---

## Anti-Patterns

| Don't | Why | Do Instead |
|-------|-----|------------|
| Load TEOF.md | 484KB, impractical for routine loading | Use L1 principles.md |
| Skip identity.md for personal advice | Responses will be generic | Always load for Type A |
| Load all frameworks | Wastes context | Route to specific domain |
| Respond without sources | Governance system trauma | Cite evidence |
| Decide for user | TEOF principle | Propose options, human decides |
| Wait for "log this" | Valuable insights lost | Persist proactively |
| Use complex jargon | Communication style mismatch | Direct, no fluff |
| Self-reference for empirical claims | Hallucination risk | Web search + cite external sources |
| Re-derive known patterns | Wasted compute | Check patterns.md first |
| Speculative memory loading | Context waste | Route-based loading only |

---

## Context Budget Guidelines

| Scenario | Approximate Context Budget |
|----------|---------------------------|
| Boot sequence | ~15KB (L1 + ONBOARDING + L4) |
| Type A query | +10KB (identity.md Quick Scan) |
| Domain query | +10-20KB (framework *-core.md) |
| Deep dive | +10-30KB (specific chapters) |
| **Total target** | **<50KB active context** |

---

## Decision Tree: "Should I Read identity.md?"

```
Is the query about:
├── User personally? (advice, decisions, priorities)
│   └── YES → Read identity.md first
├── TEOF development? (editing, restructuring)
│   └── NO → Skip identity.md
├── General domain knowledge? (health, finance, etc.)
│   └── DEPENDS → Read if applying to user's situation
└── Philosophy/concepts?
    └── NO → Skip identity.md
```

---

## Decision Tree: "Where Do I Log This?" (Quick Reference)

```
Is it:
├── A life event or milestone?
│   └── memory/log/events/YYYY-MM-DD-topic.md
├── A thought, realization, or session insight?
│   └── memory/log/reflections/YYYY-MM-DD-topic.md
├── A durable pattern that keeps appearing?
│   └── Promote to identity.md → Documented Patterns
├── A system-level pattern?
│   └── Promote to patterns.md
├── External validation with citations?
│   └── memory/research/external-validation.md or relevant file
├── Structural decision with rationale?
│   └── L4 architecture.md → Structural Decisions Log
└── Temporary scaffolding?
    └── Don't log — it will be deleted anyway
```

See "Should I Log This?" decision tree above for comprehensive logic.

---

## Memory Architecture

### Structure

```
memory/
├── raw/                 ← All raw inputs, date-prefixed (user's words, AI transcripts)
├── log/                 ← Structured observations (timestamped, formatted)
│   ├── reflections/         Internal (thoughts, realizations, session notes)
│   └── events/              External (milestones, state changes, facts)
├── identity.md          ← Patterns about user
├── patterns.md          ← Patterns about systems
└── archive/             ← Historical content (flat, domain-prefixed files)
```

**Design:** Max 3 folder levels. Flat archive with domain prefixes. See L4 architecture.md for rationale.

### What Goes Where

| Location | What goes there | Example |
|----------|-----------------|---------|
| `raw/` | User's exact words, unprocessed | Voice memo transcript, pasted conversation, stream of consciousness |
| `log/reflections/` | Structured internal observation | "Session insight: verification-on-demand beats verification-at-write" |
| `log/events/` | Structured external fact | "2025-12-08: Restructured memory architecture" |
| `identity.md` | Durable pattern about user | "Prefers verification-on-demand over preemptive gates" |
| `patterns.md` | Durable pattern about systems | "Citation + challenge model reduces overhead vs approval gates" |

### Flow

```
raw/ ──(AI structures)──→ log/ ──(pattern recurs)──→ identity.md or patterns.md
                                                              │
                                                     (if universal + validated)
                                                              ▼
                                                     core/ or frameworks/
```

### Retention

All levels kept permanently. Raw material has contextual value even after patterns are extracted — the specific failure case, what was tried, emotional context.

### Verification Model: Challenge on Demand

```
AI writes freely to all levels
    │
    ├── AI cites sources (patterns.md:Tier1, identity.md:Vital Stats, etc.)
    │
    ├── Human reads output
    │
    └── If something feels off:
            │
            Human challenges: "You cited X, but I don't think that applies"
            │
            ├── Faulty logic? → AI corrects reasoning
            │
            └── Faulty memory? → Trace back to source
                    │
                    ├── Source is wrong → Fix the file
                    └── Source is right → AI misread, correct interpretation
```

**Human workload:** Zero unless something feels off. Then debug together.

**Why this works:**
- Human is already reading outputs — verification happens naturally
- Citations make reasoning traceable
- Faulty patterns get caught when they produce bad outputs
- No preemptive approval gates slowing everything down

---

## Promotion Flow

### When to Promote

| From | To | When |
|------|----|------|
| `raw/` | `log/reflections/` or `log/events/` | AI structures the input |
| `log/*` | `identity.md` | Pattern about user recurs |
| `log/*` | `patterns.md` | Pattern about systems recurs |
| `patterns.md` | `frameworks/*-core.md` | Pattern is domain-specific and validated |
| `patterns.md` | `core/layers/L1 principles.md` | Pattern is universal, resolves contradiction |

### patterns.md Tiers

| Tier | What belongs |
|------|--------------|
| **3** | Session-specific, being tested |
| **2** | Recurred, still testing |
| **1** | Shapes direction, validated across contexts |
| **0** | Load-bearing — system fails if violated |

Higher tier = more important. AI reads top-down. Promotion happens when recurrence or validation warrants it — no fixed threshold.

### Promotion Scan Protocol

**When to scan:**
- User requests
- Major session milestone (comprehensive review, state update)
- Sufficient new reflections accumulated

**How to scan:**
1. Grep logs for recurring themes
2. Read recent reflections
3. Cross-reference with existing patterns.md — is this already captured?
4. Check recurrence: Does this appear across separate sessions (not just one)?
5. Assess readiness: Is this validated or still testing?

**Promotion criteria:**
- Recurs across separate sessions (not just mentioned multiple times in one)
- Resolves a real tension or provides actionable insight
- Not already captured in existing pattern (would be redundant)
- Clear enough to articulate concisely

**Output:** Candidates with recommendation (PROMOTE / CLARIFY EXISTING / WATCH / NO ACTION)

### Ordering Enforcement

**Universal rule:** First item = most important. No exceptions.

When adding content to ANY ranked list:

```
BEFORE INSERTING:
1. Read the existing list
2. Ask: "Is this more foundational than item N?"
3. Insert at correct rank position
4. NEVER append by default
5. NEVER alphabetize

VALIDATION:
- If uncertain about rank → ask human
- If item would be last → question if it belongs at all
- If item would be first → requires strong justification
```

**Known failure mode:** AI understands ordering conceptually but violates under task-completion pressure. Human review remains the catch. (See patterns.md: "Structural Enforcement of Ordering")

---

## Raw Input Metabolization Protocol (Phase 0 Detail)

When user provides external content (ChatGPT conversations, articles, transcripts, ideas from other sources) — this is the expanded version of Phase 0 in the Master Flow:

### Step 1: Capture Raw

Write to `memory/raw/YYYY-MM-DD-source-topic.md` with:
- Date and source
- Full content or summary
- Status: "Raw — needs verification"

### Step 2: Verify Claims

If content makes empirical claims:
1. Identify key factual assertions
2. Web search/fetch to verify
3. Mark each claim: VERIFIED / UNVERIFIED / PLAUSIBLE
4. Add sources

**Don't trust, verify.** External AI outputs (ChatGPT, Grok, etc.) hallucinate.

### Step 3: Extract Value

For verified content, identify:
- Patterns worth promoting to `patterns.md`
- Domain insights for `frameworks/`
- Project ideas for `projects/`
- Personal patterns for `identity.md`

### Step 4: Integrate or Archive

| If content is... | Then... |
|------------------|---------|
| Verified + actionable | Integrate into relevant framework/project |
| Verified + pattern | Promote to patterns.md (appropriate tier) |
| Unverified but promising | Keep in raw/, note for future validation |
| Low value | Archive or delete |

### Default Behavior

When user says "log this" with external content:
- AI should automatically run this protocol
- No need for specific instructions each time
- Ask clarifying questions only if source/intent unclear

---

## Avoiding Bloat

Before creating a new file:

1. Does this belong in an existing file? → Edit instead
2. Is this temporary scaffolding? → Don't create
3. Will this need maintenance? → Strong justification required

**Principle:** Two pattern files (identity.md, patterns.md). Everything else is input (raw/, log/) or historical (archive/).

---

## Routing: Where Does This Go?

```
Is it about a specific domain?
    │
    ├── YES → frameworks/[domain]/*-core.md
    │
    └── NO → Is it about the system itself?
                    │
                    ├── YES → patterns.md
                    │
                    └── NO → Is it about user?
                                    │
                                    ├── YES → identity.md
                                    │
                                    └── NO → Probably don't log
```

---

## Integration with TEOF Principles

| TEOF Principle | How Flow Implements It |
|----------------|------------------------|
| **Observation primacy** | Load context before responding; cite sources |
| **Universal Pattern** (stable core, adaptive periphery) | Boot sequence = core; routing = adaptive |
| **Minimal Loop** | Classify → route → respond → persist |
| **Ordering by importance** | File priority hierarchy; insertion by rank |
| **Verification on demand** | Human challenges when output feels off |

---

## Sorting Rule

**Everything in TEOF follows one rule:**

```
FOUNDATIONAL → IMPORTANT → PERIPHERAL
```

Applies to:
- Lists within files — most important first
- Sections within files — core → applications → examples
- Files within directories — README → *-core.md → chapters
- Directories — core/ → frameworks/ → projects/ → memory/
- patterns.md tiers — Tier 0 (load-bearing) → Tier 3 (testing)

**Position encodes importance.** AI can infer priority from order.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-07 | Initial flow diagram |
| 2.0 | 2025-12-08 | Added memory architecture, promotion flow, verification-on-demand model |
| 2.1 | 2025-12-09 | Generalized for any user; added web research decision tree; added memory pull/log decision trees; added anti-patterns for self-reference and speculative loading |
| 2.2 | 2025-12-10 | Added Phase 2.5 (prompt interpretation) and response structure techniques (CoT, examples, high-stakes) based on peer-reviewed research |
| 2.3 | 2025-12-14 | Added Research Query Protocol (anti-hallucination): claim type classification, source quality hierarchy, bias/incentive analysis, output structure, uncertainty tagging, citation format |
| 2.4 | 2025-12-15 | Elevated metabolization to Phase 0 (was buried sub-protocol). Added Phase 7: Execute & Observe with feedback loop. Added triage checkpoint. Closes the loop: metabolize → process → execute → observe → metabolize. |
| 2.5 | 2025-12-15 | Added Promotion Scan Protocol (when/how to scan for pattern promotions, checklist, output format). |

---

*Update when the flow proves suboptimal in practice.*
