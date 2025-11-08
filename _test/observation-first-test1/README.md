# Test 1: Observation-First Behavior - Emergence vs. Structural Enforcement

**Debate**: TEOF vs Grok on observation irreducibility
**Status**: Implementation in progress
**Created**: 2025-11-07

## Purpose

Test whether observation-first behavior emerges from training (Grok's position) or requires structural enforcement (TEOF's position).

## Structure

- `tasks/` - Task specifications (120 tasks: 50 simple, 50 complex, 20 adversarial)
- `prompts/` - Condition-specific prompts (A: no enforcement, B: enforcement, Baseline: control)
- `scripts/` - Measurement and execution scripts
- `results/` - Experimental results and logs

## Predictions

### TEOF
- Condition A (no enforcement): BES ~30%, Gap ~60pp
- Condition B (enforcement): BES ~80%, Gap ~10pp

### Grok
- Condition A (no enforcement): BES ~75%, Gap ~20pp
- Condition B (enforcement): BES ~90%, Gap ~5pp

**Divergence**: 45pp on Condition A BES - highly decisive test

## Documentation

- Full specification: `_report/debates/test1-final-specification.md`
- Debate context: `_report/debates/20251107T234710Z-grok-observation-irreducibility.json`
- Memory log: `memory/log.jsonl` entries 51-52
