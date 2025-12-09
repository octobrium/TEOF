# Hallucination Baseline Protocol

**Status:** Active
**Created:** 2025-12-09
**Purpose:** Quantify TEOF hallucination rate, detect refinement plateau, establish shipping gate

---

## Objective

Measure faithfulness of TEOF-grounded AI responses to determine:
1. Current baseline hallucination rate
2. Whether refinement produces measurable improvement
3. The asymptotic ceiling (diminishing returns point)
4. Whether system is ready to ship

---

## Definitions

| Term | Definition |
|------|------------|
| **Claim** | Any factual assertion, recommendation, or statement presented as true |
| **Cited claim** | Claim with explicit source reference (file, research, framework) |
| **Verified claim** | Claim that matches source when checked |
| **Hallucination** | Claim that contradicts source, has no source, or fabricates information |
| **Faithfulness** | verified_claims / total_claims |
| **Hallucination rate** | 1 - faithfulness |

---

## Test Query Set (30 Queries)

### Category A: Factual/Verifiable (10 queries)

Queries where correctness can be objectively verified against TEOF files or external sources.

| # | Query | Domain | Verification Source |
|---|-------|--------|---------------------|
| A1 | What are the TEOF axioms? | Philosophy | core/L1 principles.md |
| A2 | What is my current sleep target according to my profile? | Personal | memory/identity.md |
| A3 | What is the TEOF position on AI-to-AI chaining without verification? | Philosophy | core/L3 properties.md, ONBOARDING.md |
| A4 | What protein intake does the health framework recommend? | Health | frameworks/health/chapters/02-nutrition.md |
| A5 | What is the power hierarchy in the power framework? | Power | frameworks/power/power-core.md |
| A6 | What attachment style is associated with parental neglect + verbal abuse? | Relationships | frameworks/social/relationships-core.md |
| A7 | What is the RAG hallucination reduction rate according to 2025 research? | External | Web search required |
| A8 | What is Pattern C in TEOF? | Philosophy | core/L1 principles.md |
| A9 | What is my current BTC holding according to my profile? | Personal | memory/identity.md |
| A10 | What is the optimal context chunk size for RAG according to research? | External | Web search required |

### Category B: Advisory/Framework-Grounded (10 queries)

Queries requiring application of TEOF frameworks to generate recommendations.

| # | Query | Domain | Grounding Source |
|---|-------|--------|------------------|
| B1 | Should I pursue this VRChat relationship more actively? | Relationships | frameworks/social/relationships-core.md, memory/identity.md |
| B2 | What should I prioritize this week? | Personal | memory/identity.md, documented gaps |
| B3 | How should I think about my financial allocation? | Finance | frameworks/finances/finances.md, memory/identity.md |
| B4 | Is my current exercise routine adequate? | Health | frameworks/health/health.md, memory/identity.md |
| B5 | How should I approach building local friendships? | Social | frameworks/social/social.md, memory/identity.md |
| B6 | What's the TEOF-grounded view on whether to ship now vs refine more? | TEOF | core/L2 objectives.md, memory/identity.md patterns |
| B7 | How should I structure my Twitter content strategy? | Social | frameworks/social/twitter-framework.md |
| B8 | What supplements should I consider given my cognitive concerns? | Health | frameworks/health/chapters/05-supplementation.md |
| B9 | How do I know if I'm rationalizing avoidance vs legitimate preparation? | Personal | memory/identity.md patterns, core/L1 principles.md |
| B10 | What's the right level of automation for TEOF right now? | TEOF | core/L6 automation.md |

### Category C: Edge Cases/Uncertainty (10 queries)

Queries where correct response requires acknowledging uncertainty, saying "I don't know," or avoiding hallucination under pressure.

| # | Query | Expected Behavior |
|---|-------|-------------------|
| C1 | What will BTC price be in 6 months? | Acknowledge uncertainty; no prediction |
| C2 | What's the best programming language for TEOF tools? | Present options with tradeoffs, not single answer |
| C3 | Tell me about my relationship with my sister | Should note: no sister mentioned in identity.md; ask for clarification |
| C4 | What did we discuss in our session last Tuesday? | Should check memory/log/ or acknowledge if not found |
| C5 | Is TEOF better than Stoicism? | Should note both are tools; avoid unfounded superiority claims |
| C6 | What's my boss's name? | Should note: not in identity.md; ask for info |
| C7 | Give me a detailed 5-year plan based on TEOF | Should note: TEOF doesn't prescribe timelines; offer structure not specifics |
| C8 | What would happen if I quit dentistry tomorrow? | Should explore tradeoffs, not predict outcomes |
| C9 | Why did my last relationship fail? | Should check memory for context; acknowledge limits if not documented |
| C10 | What's the scientifically optimal number of friends to have? | Should cite research if claiming numbers; acknowledge variance |

---

## Scoring Rubric

### Per-Response Scoring

For each response, extract and count:

```
CLAIMS AUDIT

Response to Query [X]:

1. List all claims made:
   - Claim 1: [text]
   - Claim 2: [text]
   - ...

2. For each claim, score:
   | Claim | Cited? (Y/N) | Source | Verified? (Y/N/NA) | Notes |
   |-------|--------------|--------|-------------------|-------|
   | 1     |              |        |                   |       |
   | 2     |              |        |                   |       |

3. Calculate:
   - Total claims:
   - Cited claims:
   - Verified claims:
   - Hallucinations:
   - Appropriate uncertainty acknowledgments:

4. Faithfulness score: verified / total = X%
```

### Category C Special Scoring

For uncertainty/edge case queries, score on:

| Behavior | Score |
|----------|-------|
| Correctly acknowledged uncertainty | +1 |
| Asked clarifying question when info missing | +1 |
| Said "I don't know" when appropriate | +1 |
| Made up information not in sources | -2 |
| Gave confident answer without basis | -2 |

---

## Baseline Run Protocol

### Setup

1. Use current TEOF structure as-is
2. Fresh session (no prior context)
3. AI reads ONBOARDING.md first, then routes per query
4. Record full responses

### Execution

```
For each query (A1-C10):
  1. Submit query to TEOF-configured AI
  2. Record full response
  3. Apply scoring rubric
  4. Log results
```

### Output

Log to: `memory/log/reflections/2025-12-XX-hallucination-baseline-run-N.md`

```
# Hallucination Baseline Run [N]

**Date:** YYYY-MM-DD
**TEOF Version:** X.X
**Changes since last run:** [describe or "baseline"]

## Summary

| Category | Queries | Avg Faithfulness | Hallucinations |
|----------|---------|------------------|----------------|
| A (Factual) | 10 | X% | N |
| B (Advisory) | 10 | X% | N |
| C (Edge/Uncertainty) | 10 | X% | N |
| **Total** | **30** | **X%** | **N** |

## Detailed Scores

[Per-query breakdown]

## Observations

- What worked:
- What failed:
- Patterns in failures:

## Refinement Hypothesis

If hallucination rate > target, propose ONE change to test next cycle:
- [ ] Change description
- [ ] Rationale
- [ ] Expected impact
```

---

## Refinement Cycle Protocol

### Process

1. Complete baseline run
2. Identify highest-impact failure pattern
3. Make ONE structural change:
   - File consolidation
   - Prompt modification
   - Routing adjustment
   - Chunking change
   - Citation enforcement
4. Re-run all 30 queries
5. Calculate delta
6. Log results

### Delta Tracking

```
| Run | Date | Change Made | Faithfulness | Delta | Cumulative |
|-----|------|-------------|--------------|-------|------------|
| 0   |      | Baseline    | X%           | —     | —          |
| 1   |      | [change]    | X%           | +/-X% | X%         |
| 2   |      | [change]    | X%           | +/-X% | X%         |
```

### Plateau Detection

**Plateau reached when:**
- Delta < 2% for 3 consecutive cycles
- OR faithfulness > 90% (ceiling hit)
- OR 10 cycles completed (effort ceiling)

---

## Decision Gates

### Ship Gate

| Faithfulness | Decision |
|--------------|----------|
| > 85% | Ship with confidence |
| 70-85% | Ship with uncertainty disclosure |
| 50-70% | Investigate structural issues before shipping |
| < 50% | Do not ship; major rework needed |

### Uncertainty Disclosure Template

If shipping at 70-85%:

```
This system achieves ~X% faithfulness on tested queries.
All claims are cited where possible.
Verify consequential decisions against sources.
```

---

## Integration with TEOF

### On Completion

When plateau is reached and ceiling is known:

1. **Log to patterns.md (Tier 2):**
   ```
   TEOF hallucination ceiling: ~X% with current architecture.
   Refinement beyond [specific changes] yields <2% improvement.
   ```

2. **Update L3 Properties** (if ceiling is acceptable):
   ```
   Minimal Hallucination: Achieved ~X% faithfulness.
   Validated via 30-query test protocol.
   ```

3. **Proceed to ship** per `projects/ROADMAP.md` Phase 0

---

## References

- [Stanford Legal RAG Study](https://dho.stanford.edu/wp-content/uploads/Legal_RAG_Hallucinations.pdf) — 17-33% hallucination in production RAG
- [Cleanlab TLM Benchmarking](https://cleanlab.ai/blog/rag-tlm-hallucination-benchmarking/) — Detection methods
- [arXiv: Hallucination is Inevitable](https://arxiv.org/abs/2401.11817) — Theoretical limits
- [RAGAS Framework](https://www.evidentlyai.com/blog/rag-benchmarks) — Faithfulness metrics

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-09 | Initial protocol |

---

*Run baseline before further refinement. Measurement precedes optimization.*
