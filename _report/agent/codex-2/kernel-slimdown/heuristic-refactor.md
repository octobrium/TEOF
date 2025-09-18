# Kernel Slimdown — Shared Heuristics Refactor (S2)

## Changes
- Extended `extensions/validator/ocers_rules.py` with shared pattern hints (`RISK_TERMS`, `MANUAL_RECOVERY_TERMS`, `REFERENCE_TERMS`, `TOOL_TERMS`) and a `contains_any` helper for case-insensitive substring checks.
- Rewired `teof/eval/ocers_min.py` to consume those shared helpers, removing its local `_contains` implementation and aligning risk/tool/reference detection with the validator heuristics.
- Ensured evaluator behaviour remains stable by rerunning `pytest tests/test_ocers_eval.py tests/test_brief.py` (passes locally).

## Impact
- Eliminates duplicate pattern definitions across validator/evaluator stacks.
- Future heuristic updates can land in `ocers_rules` once and propagate to both pipelines.
- Sets up S3 work to add dedicated unit coverage for the shared module and refresh deterministic receipts.
