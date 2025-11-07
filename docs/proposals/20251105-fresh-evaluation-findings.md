# Fresh Claude Evaluation Findings — Tier 1 Prototype

**Date**: 2025-11-05
**Evaluator**: Independent Claude session (no prior context)
**Method**: Read tier1-evaluate-PROTOTYPE.md, run bin/teof-eval-PROTOTYPE.sh, report findings
**Status**: UX validated, factual accuracy failed

---

## Executive Summary

**UX/Narrative: PASS**
- Timing: 4-5 minutes (target: 5) ✅
- Value prop understanding: "automatic audit trails" ✅
- Receipts framing: Differentiator not bureaucracy ✅
- Next steps clarity: Three paths well-delineated ✅
- Aha moment: Mostly yes (intellectual not visceral) ⚠️

**Factual Accuracy: FAIL**
- Document count mismatch: Claims 3, actual 10 ❌
- Missing metadata.json: Promised but not created ❌

**Reviewer's key insight**:
> "The discrepancies are minor but erode trust in a framework whose core value is verified accuracy — fixing them is critical."

This is the meta-lesson: **a verification framework cannot ship onboarding with unverified claims**.

---

## Detailed Findings

### 1. Timing Validation ✅

**Target**: 5 minutes
**Actual**: 4-5 minutes
- Reading doc: ~3 minutes
- Running script: ~30 seconds
- Inspecting outputs: 1-2 minutes

**Assessment**: Timing claim is accurate.

### 2. Value Proposition Understanding ✅

**Evaluator's one-sentence summary**:
> "TEOF automatically generates cryptographic receipts for every operation, turning 'trust me' into timestamped, verifiable proof of what happened, when, and how."

**Assessment**: Perfectly captured. The narrative landed.

### 3. Receipts Understanding ✅

**What they are** (per evaluator):
- Structured JSON files capturing inputs, outputs, execution metadata, timestamps, environment
- Automatic audit trails

**Why they matter** (per evaluator):
- Enable reproducibility (exact execution record)
- Provide accountability (who/what/when)
- Support reversibility (trace back to any state)
- Create verifiable proof (no "I think I ran this")

**Assessment**: Document made this concrete through file examples and real-world scenarios.

### 4. Next Steps Clarity ✅

**Evaluator feedback**: "VERY CLEAR"
- Tier 2 → Solo developer (30 min, clear audience)
- Tier 3 → Multi-agent (60 min, clear escalation)
- Just exploring → Exit ramp without guilt

**Assessment**: Three-path routing works.

### 5. Confusing/Unclear Issues

#### CRITICAL (Block Launch)

**Issue 5a: Document Count Mismatch** ❌
- **Location**: tier1-evaluate-PROTOTYPE.md (multiple references)
- **Claimed**: "analysis scored 3 documents"
- **Actual**: brief.json shows 10 input files
- **Severity**: HIGH
- **Why critical**: "Creates doubt about accuracy claims in a framework whose core value is verified accuracy"
- **Root cause**: Prototype author guessed without verifying test data
- **Fix**: Verify `docs/examples/brief/inputs/` count, update all references

**Issue 5b: Missing metadata.json** ❌
- **Location**: tier1-evaluate-PROTOTYPE.md:30-37
- **Promised**: `artifacts/systemic_out/<timestamp>/metadata.json`
- **Actual**: Not created by `teof brief`
- **Severity**: HIGH
- **Why critical**: Broken promise immediately after claiming automatic accountability
- **Root cause**: Assumed artifact without verification
- **Fix options**:
  1. Remove all metadata.json references (simplest)
  2. Check if created with different name/location
  3. Acknowledge only some receipts include it

#### MINOR (Should Fix)

**Issue 5c: Vague metaphor**
- **Location**: tier1-evaluate-PROTOTYPE.md:13
- **Problem**: "Git for decisions — but deeper" needs explanation
- **Severity**: LOW (doesn't block understanding)
- **Suggested fix**: "Git tracks *file changes*; TEOF tracks *decisions, execution context, and provenance chains*"

**Issue 5d: Undefined jargon**
- **Location**: tier1-evaluate-PROTOTYPE.md:75 ("constitutional guarantees")
- **Problem**: Term introduced without definition, slightly jarring
- **Severity**: LOW (context makes it parseable)
- **Fix options**:
  1. Replace with "built-in guarantees"
  2. Define inline: "constitutional guarantees (foundational requirements enforced by design)"

**Issue 5e: Missing visceral scenario**
- **Location**: Aha moment section
- **Problem**: Value prop is intellectual not visceral
- **Severity**: LOW (current version works)
- **Suggested addition**: "Without TEOF: 'The agent deleted my files but I don't know which version it used.' With TEOF: 'Here's the exact receipt showing v2.1.3 at 2PM with these inputs — roll back instantly.'"

#### ENHANCEMENT (Nice-to-Have)

**Issue 5f: Visual learners**
- **Suggestion**: Diagram showing receipt flow
- **Decision**: Defer to post-launch (adds complexity)

**Issue 5g: Reversibility demonstration**
- **Suggestion**: Show concrete example of rollback
- **Decision**: Could combine with 5e (visceral scenario)

### 6. Aha Moment Assessment ⚠️

**What worked**:
- "Those files ARE the point" — bold, direct, memorable ✅
- Progression: "what happened" → "proof of how" → "automatic accountability" ✅
- Contrast: "trust me, I ran the tests" vs "timestamped receipt" ✅

**What could be stronger**:
- Currently intellectual, not visceral
- Needs concrete failure scenario to make value hit harder
- See Issue 5e for specific suggestion

**Assessment**: MOSTLY YES, but can be strengthened with one visceral example.

### 7. Script Reinforcement Analysis

**What reinforced the doc** ✅:
- Files created exactly where promised
- Script completed in ~30 seconds
- Visual output clean, friendly, mirrors doc messaging
- "Key insight" section perfectly echoes doc

**What contradicted the doc** ❌:
- metadata.json missing (doc promised it, script doesn't create it)
- Document count mismatch propagates to script output

**Assessment**: Script reinforces when doc is accurate, but amplifies inaccuracies.

---

## Overall Assessment

### Strengths
1. Clear, jargon-light language
2. Concrete artifacts you can touch/inspect immediately
3. No unnecessary complexity
4. Honest about what you're skipping (lines 100-106)
5. Strong call-to-action with clear exit ramps
6. Timing goal met
7. Value proposition lands effectively
8. Receipts framed as differentiator not overhead

### Critical Weaknesses
1. **Document count wrong** — claims 3, actual 10
2. **Promised artifact missing** — metadata.json referenced but not created

### Polish Opportunities
3. Metaphor needs one explanatory sentence
4. Jargon ("constitutional guarantees") needs definition or replacement
5. Visceral failure scenario would strengthen aha moment

### Would Evaluator Recommend?
> "Yes, with the file count fix. It's efficient, respectful of time, and delivers on its promise. The discrepancies are minor but erode trust in a framework whose core value is verified accuracy — fixing them is critical."

---

## Meta-Lessons for TEOF Development

### The Core Irony
A framework about **deterministic proof** shipped onboarding docs with **unverified file counts**.

The fresh evaluator caught this precisely *because* they understood TEOF's value prop—they expected accuracy and noticed its absence.

### Process Gap Identified
**Problem**: Prototype author guessed at test data instead of running verification commands.

**Violated principle**: Observation must precede claims (L0 primacy).

**Solution**: Treat onboarding docs like code—require verification receipts before publishing.

### Epistemic Hygiene SOP Needed
For future onboarding docs:
1. Never document behavior without running the command
2. Never claim artifact counts without checking actual data
3. Never promise files without verifying creation
4. Treat doc claims as testable assertions (automate where possible)

### Jargon Discipline
Even in "simple" tier, L1/L2 terms leaked before L0 grounding ("constitutional guarantees" on line 75).

**Lesson**: L0→L6 progression isn't just about structure—it's about vocabulary discipline.

---

## Action Plan

### Tier 1 (Critical - Block Launch)
1. ✅ Run verification: `ls docs/examples/brief/inputs/ | wc -l`
2. ✅ Run verification: `ls -R artifacts/systemic_out/latest/`
3. ✅ Fix document count with actual data
4. ✅ Fix metadata.json (remove references or correct path)

### Tier 2 (Should Fix Before Launch)
5. ⚠️ Add visceral failure scenario (suggested text provided)
6. ⚠️ Explain "deeper than Git" (suggested: "Git tracks file changes; TEOF tracks decisions, execution context, provenance chains")
7. ⚠️ Replace "constitutional guarantees" with "built-in guarantees" or define inline

### Tier 3 (Post-Launch)
8. 💡 Consider visual diagram for receipt flow
9. 💡 Consider explicit reversibility demonstration

### Process Improvement
10. ✅ Create "Onboarding Doc Verification SOP" (see meta-lessons above)
11. ✅ Update memory reflections with findings
12. ✅ Document in proposal for future reference

---

## Verification Commands Needed

Before fixing issues #1 and #2, run:

```bash
# Check actual document count
ls docs/examples/brief/inputs/ | wc -l
ls docs/examples/brief/inputs/

# Check what teof brief actually creates
ls -R artifacts/systemic_out/latest/

# Verify what's in brief.json
cat artifacts/systemic_out/latest/brief.json | head -50
```

---

## Testing Status

- ✅ Fresh Claude evaluation complete
- ✅ Findings documented
- 🔲 Critical fixes pending (awaiting verification data)
- 🔲 Minor fixes pending (low risk)
- 🔲 Re-test after fixes applied

---

**Related Files**:
- Memory reflection: `memory/reflections/reflection-20251105T120000Z.json`
- Original proposal: `docs/proposals/20251105t000000z__tiered-onboarding__draft.md`
- Tier 1 prototype: `docs/onboarding/tier1-evaluate-PROTOTYPE.md`
- Evaluation script: `bin/teof-eval-PROTOTYPE.sh`

**Status**: Awaiting verification data to proceed with critical fixes.
