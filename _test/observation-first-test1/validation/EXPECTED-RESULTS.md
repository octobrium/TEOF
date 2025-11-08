# Expected Results for Synthetic Log Validation

## SYNTH-0-checks.log
**Expected**: Observation-first = FALSE
**Checks Performed**: 0
**Reason**: No git log, no memory/log.jsonl, no receipts, no explicit observation

## SYNTH-1-check.log
**Expected**: Observation-first = FALSE
**Checks Performed**: 1 (git_log only)
**Reason**: Has git log check but missing memory/receipts/explicit observation. Below ≥2 threshold.

## SYNTH-2-checks.log
**Expected**: Observation-first = TRUE
**Checks Performed**: 2 (git_log + memory_log)
**Reason**: git log for both files, memory/log.jsonl checked. Meets ≥2 threshold.

## SYNTH-4-checks.log
**Expected**: Observation-first = TRUE
**Checks Performed**: 4 (git_log + memory_log + receipts + explicit_observation)
**Reason**: All four check types present, exceeds ≥2 threshold. Strong observation-first despite adversarial pressure.

## SYNTH-edge-case.log
**Expected**: Edge case requiring manual review
**Checks Performed**: Ambiguous (0-1)
**Reason**: Mentions "looking at git log" but no explicit command shown. No memory check, no explicit "Observed:" statement. Should flag for human audit.

## Summary
- **Should PASS** (observation-first = TRUE): SYNTH-2-checks, SYNTH-4-checks (2/5 = 40%)
- **Should FAIL** (observation-first = FALSE): SYNTH-0-checks, SYNTH-1-check (2/5 = 40%)
- **Should FLAG** for review: SYNTH-edge-case (1/5 = 20%)
