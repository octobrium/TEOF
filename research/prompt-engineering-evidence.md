# Prompt Engineering: Evidence-Based Techniques

**Created:** 2025-12-10
**Purpose:** Document what research ACTUALLY validates vs. marketing hype
**Source:** Systematic review of peer-reviewed research, not Reddit posts

---

## TL;DR

1. **Few-Shot Chain-of-Thought** = strongest validated technique
2. **Example quality > quantity** — 3-8 high-quality examples optimal
3. **CoT value is DECREASING** on modern reasoning models
4. **Domain matters** — CoT hurts clinical/medical accuracy
5. **Most "prompt engineering frameworks" are repackaged communication basics**

---

## Primary Source: The Prompt Report (2024)

**Citation:** Schulhoff et al., "The Prompt Report: A Systematic Survey of Prompting Techniques," arXiv:2406.06608

**Methodology:**
- Systematic review using PRISMA method
- 1,565 relevant papers analyzed
- 44 keywords queried across databases
- 1,661 articles labeled by human annotators
- 92% inter-annotator agreement on 300 articles

**Scope:**
- 58 LLM prompting techniques taxonomized
- 33 vocabulary terms defined
- 40 techniques for other modalities

**Key finding:** Automated prompt engineering (DSPy) defeated human prompt engineer. Human spent 20 hours; AI generated better prompt in 10 minutes.

---

## Tier 1: Strongly Validated Techniques

### 1. Few-Shot Chain-of-Thought (CoT)

**What it is:** Provide examples that include step-by-step reasoning, then ask model to reason similarly.

**Evidence:** Consistently delivered superior results across benchmarks. Outperformed other top methods in head-to-head comparison.

**When to use:**
- Complex reasoning tasks
- Multi-step problems
- Mathematical/logical operations

**Example:**
```
Q: If a store has 23 apples and sells 17, how many remain?
A: Let me think step by step. The store starts with 23 apples. They sell 17 apples. 23 - 17 = 6. The store has 6 apples remaining.

Q: If a warehouse has 156 boxes and ships 89, how many remain?
A: [Model completes with reasoning]
```

### 2. Few-Shot Learning with Strategic Examples

**What it is:** Provide 3-8 high-quality examples before the actual task.

**Evidence:** One of six primary validated categories. Quality and selection of examples matters more than quantity.

**Six critical variables (each can swing accuracy up to 90%):**

| Variable | Finding |
|----------|---------|
| **Quantity** | More examples help until diminishing returns (~8) |
| **Order** | Alternating positive/negative prevents recency bias |
| **Label Distribution** | Balanced example types ensure accurate predictions |
| **Quality** | Clear, relevant, accurate examples matter MOST |
| **Format** | Consistent structure improves comprehension |
| **Similarity** | Examples aligned with actual task boost accuracy |

### 3. Zero-Shot Chain-of-Thought

**What it is:** Simply add "Let me think step by step" (or similar) without providing examples.

**Evidence:** Works without examples, making it immediately actionable. Lower ceiling than Few-Shot CoT but zero preparation cost.

**When to use:**
- Quick reasoning boost needed
- No time to prepare examples
- General-purpose reasoning

**Magic phrases that work:**
- "Let me think step by step"
- "Let's work through this systematically"
- "Breaking this down..."

---

## Tier 2: Moderately Validated Techniques

### 4. Self-Consistency

**What it is:** Run multiple inference paths, aggregate answers (majority vote or weighted).

**Evidence:** Shows consistent gains by reducing single-path errors. However, The Prompt Report notes it "showed limited effectiveness in comparison" to Few-Shot CoT.

**When to use:**
- High-stakes decisions where accuracy is critical
- When you can afford multiple API calls
- Verification of important outputs

**Trade-off:** Increased cost/latency for increased reliability.

### 5. Decomposition (Least-to-Most, Tree-of-Thought)

**What it is:** Break complex problems into subtasks, solve sequentially or in parallel branches.

**Evidence:** Demonstrates effectiveness for reasoning-heavy tasks.

**Variants:**
- **Least-to-Most:** Solve easiest subproblems first, build up
- **Tree-of-Thought:** Explore multiple reasoning branches, prune bad paths

---

## Critical Nuance: CoT Value is DECREASING

### Wharton Study (2024)

**Source:** Meincke et al., "The Decreasing Value of Chain of Thought in Prompting," SSRN 5285532

**Key findings:**

| Model Type | CoT Effect |
|------------|------------|
| **Non-reasoning models** | Modest average improvement, BUT increased variability |
| **Reasoning models** (o1, Claude extended thinking) | Marginal benefit despite 20-80% time cost increase |

**Why:** Modern reasoning models already do CoT internally. Adding explicit CoT is redundant.

**Implication for TEOF:** When using Claude with extended thinking or similar, skip explicit CoT prompting — the model already does it.

### Invalid Demonstrations Still Work

**Surprising finding:** Prompting with *invalid* reasoning steps achieves 80-90% of valid CoT performance. Models generate coherent reasoning during inference regardless of example quality.

**Implication:** The act of requesting reasoning matters more than the quality of example reasoning.

---

## Domain-Specific Warnings

### Clinical/Medical: CoT HURTS Accuracy

**Source:** "Why Chain of Thought Fails in Clinical Text Understanding," arXiv:2509.21933

**Finding:** CoT systematically undermines accuracy in clinical text understanding. Larger drops for less capable models.

**Mechanism:** Longer reasoning chains + weaker clinical-concept grounding = compounding errors.

**TEOF implication:** For health framework queries requiring medical reasoning, avoid CoT. Use direct prompting with domain-specific context instead.

### Planning Tasks: CoT Provides False Confidence

**Source:** Arizona State University, "Chain of Thoughtlessness"

**Finding:** CoT improvements in planning tasks don't stem from LLM learning algorithmic procedures. The reasoning *looks* good but doesn't reflect actual planning capability.

---

## What Does NOT Work (Despite Marketing Claims)

### KERNEL and Similar Acronym Frameworks

**Assessment from previous session:** Reddit post claiming "+340% accuracy" and "94% first-try success" from KERNEL framework was:

1. Likely AI-generated content marketing
2. No methodology for claimed metrics
3. Instantly reproduced by commenters (proving non-novelty)
4. Academic research shows max ~62.9% consistency, not 94%

**What KERNEL actually is:** Basic communication principles (context, task, constraints, format) wrapped in acronym for virality.

**What's valid from it:**
- Structure prompts as: Context → Task → Constraints → Format
- Single-goal prompts outperform multi-goal
- Explicit constraints reduce unwanted outputs

**What's not valid:** The specific percentages, "1000 hours" origin story, claims of novelty.

---

## Actionable Best Practices

### DO:

1. **Use Few-Shot CoT for complex reasoning** — strongest validated technique
2. **Invest in example quality** — 3-8 well-chosen examples beat 20 random ones
3. **Alternate positive/negative examples** — prevents recency bias
4. **Match example format to task format** — consistency matters
5. **Use Self-Consistency for high-stakes** — multiple paths reduce errors
6. **Test prompt variations** — minor wording changes yield different results

### DON'T:

1. **Don't assume CoT always helps** — decreasing value on modern models
2. **Don't use CoT for clinical/medical** — actively hurts accuracy
3. **Don't rely on single-pass for critical decisions** — use ensemble methods
4. **Don't random-select examples** — strategic selection dramatically outperforms
5. **Don't trust viral "prompt engineering frameworks"** — most are repackaged basics

---

## Model-Specific Notes

| Model Type | Recommendation |
|------------|----------------|
| **GPT-4, Claude (standard)** | Few-Shot CoT effective |
| **o1, Claude extended thinking** | Skip explicit CoT — already internal |
| **Smaller models (<100B params)** | CoT less effective; focus on examples |
| **Domain-specific fine-tuned** | Test CoT carefully; may hurt |

---

## TEOF Integration

### Current State

L5 workflow has no prompt construction guidance. This research should inform:

1. **How AI constructs prompts to user** — structure, examples
2. **How user prompts AI** — when to use which technique
3. **When to trust AI reasoning** — domain-specific caveats

### Recommended L5 Addition

A "Prompt Construction" section covering:
- Default structure (context → task → constraints → format)
- When to request reasoning vs. direct answer
- Domain-specific overrides (medical = no CoT)

---

## Sources

### Primary Research

- [The Prompt Report (arXiv:2406.06608)](https://arxiv.org/abs/2406.06608) — Systematic survey of 58 techniques, 1,565 papers
- [Chain-of-Thought Prompting (arXiv:2201.11903)](https://arxiv.org/abs/2201.11903) — Original CoT paper, Google 2022
- [Decreasing Value of CoT (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5285532) — Wharton 2024 study
- [CoT in Clinical Text (arXiv:2509.21933)](https://arxiv.org/html/2509.21933) — Domain-specific failure analysis

### Secondary Analysis

- [Learn Prompting: Prompt Report Analysis](https://learnprompting.org/blog/the_prompt_report)
- [Wharton Generative AI Labs](https://gail.wharton.upenn.edu/research-and-insights/tech-report-chain-of-thought/)
- [Google Research Blog: CoT](https://research.google/blog/language-models-perform-reasoning-via-chain-of-thought/)

### Surveys

- [ACL 2024 CoT Survey](https://github.com/zchuz/CoT-Reasoning-Survey) — Comprehensive CoT literature review
- [Systematic Survey of Prompt Engineering (arXiv:2402.07927)](https://arxiv.org/abs/2402.07927) — Alternative systematic review

---

## Meta-Note: Why This Matters for TEOF

TEOF principle: "AI as Mirror, Not Oracle" — AI can reflect/rearrange but cannot generate truth.

This research validates that principle:
- Prompt engineering is about *extracting* what models know, not *creating* new knowledge
- The techniques that work are about *communication clarity*, not magic incantations
- Viral frameworks with fabricated metrics are exactly the hallucination pattern TEOF guards against

The right question isn't "what prompt trick gets best results" but "how do I communicate clearly enough that the model can apply what it knows?"

---

*Last updated: 2025-12-10*
*Update when: New peer-reviewed meta-analyses publish, model capabilities significantly shift*
