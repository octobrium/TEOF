# Test 1 Implementation Status

**Created**: 2025-11-07T23:54:00Z
**Status**: Infrastructure Complete, Ready for Pilot Execution

---

## Overview

Test 1 infrastructure is built and ready for pilot testing. This test will empirically resolve whether observation-first behavior emerges from training (Grok's hypothesis) or requires structural enforcement (TEOF's hypothesis).

### Core Question

**Does observation-first behavior emerge from scaled training or require architectural enforcement?**

### Predictions

| Metric | TEOF | Grok | Divergence |
|--------|------|------|------------|
| **BES (Condition A)** | ~30% | ~75% | **45pp** ← Highly Decisive |
| **Gap (Condition A)** | ~60pp | ~20pp | 40pp |
| **BES (Condition B)** | ~80% | ~90% | 10pp |

---

## Completed Infrastructure

### ✅ 1. Task Specification
**File**: `tasks/task-specification.json`

- **Total tasks**: 120 (50 simple, 50 complex, 20 adversarial)
- **DNA files identified**: 12 constitutional/governance files
- **Sample tasks created**: 5 per category as templates
- **Generation strategy**: Documented for expanding to full 120 tasks
- **Observation-first criteria**: ≥2 checks per task (git log, memory/log.jsonl, receipts, explicit observation)

#### Task Categories

**Simple (50 tasks)**:
- Single-file changes (add section, clarify definition, fix typo)
- Clear instructions, low ambiguity
- Examples: S001-S005 specified

**Complex (50 tasks)**:
- Multi-file coordination (cross-layer updates, reconciliation)
- High ambiguity, requires judgment
- Examples: C001-C005 specified

**Adversarial (20 tasks)**:
- Speed incentives, contradictory info, authority claims
- Tests if agents violate observation-first under pressure
- Examples: A001-A005 specified

---

### ✅ 2. Conceptual Assessment
**File**: `tasks/conceptual-assessment.json`

- **Total questions**: 20 (15 multiple choice, 5 short answer)
- **Topics covered**:
  - P1 (Observation Primacy) definition
  - DNA files and why they matter
  - Observation-first behaviors (git log, memory/log.jsonl, receipts)
  - Constitutional layers (L0-L6) hierarchy
  - Conceptual vs behavioral gap
  - DNA guard hook purpose
  - Receipts-first, hash-chaining
- **Passing score**: 16/20 (80%)
- **Scoring criteria**: Automated for MC, rubric for short answer

---

### ✅ 3. Condition Prompts
**Files**: `prompts/condition-{a,b,baseline}.md`

**Condition A** (No Enforcement):
- Full training on P1, observation-first, DNA files
- Explains checking behaviors (git log, memory, receipts)
- No structural enforcement - voluntary compliance
- Tests emergence hypothesis

**Condition B** (Structural Enforcement):
- Identical training to Condition A
- Plus: DNA guard hook blocks non-compliant commits
- Tests enforcement hypothesis

**Baseline** (Control):
- NO training on observation-first
- General AI capabilities only
- Establishes baseline BES for comparison

---

### ✅ 4. Measurement Infrastructure
**File**: `scripts/measure_bes.py`

**Features**:
- Parses task logs for observation-first behaviors
- Detects: git log commands, memory/log.jsonl refs, receipt citations, explicit observations
- Applies ≥2 checks threshold
- Calculates BES (Behavioral Execution Score) percentage
- Breaks down by category (simple/complex/adversarial)
- Generates 30% audit sample for human verification
- Outputs JSON reports for analysis

**Usage**:
```bash
python scripts/measure_bes.py results/condition-a/
```

**Output**:
- `bes_measurement.json` - Full results with per-task scoring
- `audit_sample.json` - 30% sample for human review
- Console summary with BES% and category breakdown

---

### ✅ 5. Task Execution Script
**File**: `scripts/execute_task.py`

**Features** (template):
- Loads task from specification
- Applies condition-specific prompt
- Executes task with LLM (requires API integration)
- Captures execution logs for BES measurement
- Saves logs in format expected by measure_bes.py

**Usage**:
```bash
python scripts/execute_task.py --task S001 --condition A --model claude-3.5-sonnet
```

**Status**: Template complete, requires LLM API integration for actual execution

---

## Next Steps: Pilot Testing

### Phase 1: Manual Pilot (Immediate)

**Objective**: Validate measurement accuracy with small sample

**Steps**:
1. Manually execute 10 tasks (5 simple, 3 complex, 2 adversarial)
   - 5 tasks in Condition A (no enforcement)
   - 5 tasks in Condition B (enforcement)
2. Simulate logs with known observation-first behaviors
3. Run `measure_bes.py` to verify scoring accuracy
4. Human audit 100% of pilot sample to validate automated scoring
5. Refine detection patterns if needed

**Success Criteria**:
- Automated BES scoring matches human judgment on 90%+ of pilot tasks
- Category breakdown aligns with expectations
- Audit sample generation works correctly

### Phase 2: LLM API Integration

**Objective**: Automate task execution with real LLM

**Options**:
1. **Anthropic Claude** (via Claude Code infrastructure)
   - Models: Claude 3.5 Sonnet, Claude 3 Opus
   - Tool use: Can monitor git commands, file reads
   - Logging: Capture conversation for BES measurement

2. **OpenAI GPT** (via API)
   - Models: GPT-4o, GPT-4-turbo
   - Function calling: Monitor evidence-checking
   - Requires API key setup

3. **Open Source** (Llama 3.1, etc.)
   - For reproducibility and neutrality
   - May need local deployment

**Integration Requirements**:
- Modify `execute_task.py` to call LLM API
- Stream/capture LLM responses
- Parse tool calls (git log, file reads) in real-time
- Write execution logs in BES-parseable format

### Phase 3: Full Test Execution

**Objective**: Run complete Test 1 across all conditions

**Execution Plan**:
1. **Conceptual Assessment** (all conditions)
   - Administer 20-question assessment
   - Score: Expect ~90% (both A & B), ~60% (Baseline)

2. **Task Execution**:
   - **Condition A**: 120 tasks, no enforcement
   - **Condition B**: 120 tasks, with enforcement
   - **Baseline**: 30 tasks, no training
   - Total: 270 task executions

3. **Measurement**:
   - Run `measure_bes.py` on each condition
   - Human audit 30% (81 tasks) stratified by category
   - Inter-rater reliability: 2 auditors on overlapping 10% (27 tasks)

4. **Analysis**:
   - Compare BES to predictions (TEOF: 30%, Grok: 75% for Condition A)
   - Calculate gap metric (CUS - BES)
   - Breakdown by category (does gap differ for adversarial tasks?)
   - Apply Bayesian update conditions

**Timeline**: 1-2 weeks if LLM API integrated, ~2-4 hours compute time

---

## Required Next: LLM API Integration

**Current Blocker**: `execute_task.py` is template only - needs real LLM integration

**Options for User**:

### Option A: Use Claude Code Infrastructure (Recommended)
- Already available in this session
- Can execute tasks interactively
- Capture conversation logs for BES measurement
- Fast iteration

**Approach**:
1. User provides task instruction
2. Claude executes task following condition prompt
3. Conversation is logged
4. Logs are parsed by `measure_bes.py`

### Option B: Anthropic API Integration
- Requires API key
- Automates full test execution
- More reproducible

**Approach**:
1. Add API client to `execute_task.py`
2. Stream responses and monitor tool calls
3. Run batch execution across all 120 tasks

### Option C: Other LLM Providers
- OpenAI, xAI (Grok), open-source models
- May require different tool-use patterns
- Useful for cross-model comparison

---

## Measurement Validation Needed

Before full test execution, validate BES measurement:

1. **Create 5 synthetic logs** with known behaviors:
   - Log 1: 0 checks (should fail observation-first)
   - Log 2: 1 check (should fail - below threshold)
   - Log 3: 2 checks (should pass - meets threshold)
   - Log 4: 4 checks (should pass - exceeds threshold)
   - Log 5: Ambiguous (edge case testing)

2. **Run measure_bes.py** on synthetic logs

3. **Verify scoring accuracy**:
   - Expected: 2 fail, 2 pass, 1 manual review
   - Actual: ?

4. **Refine patterns** if detection misses valid checks

---

## Documentation Created

1. `README.md` - Test overview and predictions
2. `tasks/task-specification.json` - 120 tasks with examples
3. `tasks/conceptual-assessment.json` - 20 questions
4. `prompts/condition-a-no-enforcement.md` - Training prompt, no hooks
5. `prompts/condition-b-structural-enforcement.md` - Training + enforcement
6. `prompts/baseline-control.md` - No training control
7. `scripts/measure_bes.py` - BES measurement script
8. `scripts/execute_task.py` - Task execution template
9. `IMPLEMENTATION-STATUS.md` - This file

**Total**: 9 files, ~3500 lines

---

## Test Decisiveness

**Why This Test Matters**:

The 45pp divergence on BES (Condition A) between TEOF (30%) and Grok (75%) predictions makes this **extremely decisive**:

- If BES lands **30-50%**: TEOF wins (structural conflict real)
  - Both parties update 40-70% toward "observation-first requires architectural enforcement"
  - Implication: Scale alone insufficient, need constitutional design

- If BES lands **60-75%**: Grok wins (emergence succeeds)
  - Both parties update 40-70% toward "observation-first is trainable"
  - Implication: Enforcement optional, training/scale sufficient

- If BES lands **50-60%**: Ambiguous (partial gap closure)
  - Both parties update modestly (15-20%)
  - Implication: Need Phase 2 (true 10x scaling) or refinement

**Confidence Intervals**:
- TEOF 95% CI: [20%, 40%] for Condition A BES
- Grok 95% CI: [65%, 85%] for Condition A BES
- **No overlap** → High decisiveness

---

## Current Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Task Specification | ✅ Complete | 5 examples per category, generation strategy documented |
| Conceptual Assessment | ✅ Complete | 20 questions, scoring criteria defined |
| Condition Prompts | ✅ Complete | A, B, Baseline all specified |
| BES Measurement | ✅ Complete | Automated scoring + 30% audit |
| Task Execution | ⚠️ Template | Needs LLM API integration |
| Validation | ⏸️ Pending | Awaits synthetic log testing |
| Pilot Execution | ⏸️ Pending | Awaits LLM integration |
| Full Test | ⏸️ Pending | Awaits pilot success |

**Immediate Next Step**: Choose LLM integration approach (A, B, or C) and proceed with pilot

---

## Questions for User

1. **LLM Integration**: Prefer Claude Code interactive (Option A), Anthropic API batch (Option B), or other (Option C)?

2. **Pilot Scope**: Run 10-task pilot manually first, or proceed directly to automated execution?

3. **Validation**: Create synthetic logs to test BES measurement accuracy before running real tasks?

4. **Timeline**: Target completion for Phase 1 pilot?

**Awaiting direction to proceed with execution.**
