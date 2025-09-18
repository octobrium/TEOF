# Kernel Slimdown — Heuristic Audit (S1)

## Scope
- Compare `extensions/validator/teof_ocers_min.py` (news-style heuristic validator) with `teof/eval/ocers_min.py` (queue/proposal evaluator).
- Identify shared primitives worth centralising.
- Surface divergence that should remain (different inputs / scoring scales).

## Findings
1. **Normalization & pattern detection duplicated.**
   - Both implementations lower-case, strip whitespace, and rely on regex token hits (evidence, attribution, fallback, etc.).
   - Validator used ad-hoc helpers (`norm_text`, `count_patterns`) while evaluator reimplemented similar checks (`_contains`, regex lists).
   - **Action:** centralised validator heuristics into `extensions/validator/ocers_rules.py`; exposes `norm_text`, `count_patterns`, and OCERS scorers for reuse.

2. **Pillar intent differs by input contract.**
   - Validator (news text) scores 1–5 per pillar with journalism-tuned features (quotes, attributions, numbers) and aggregates to PASS/NEEDS WORK thresholds.
   - Evaluator (queue plans) expects headed sections (`Goal:`, `Fallback:`) and maps to 0–2 per pillar; emphasis on structural compliance (sections present, references).
   - **Conclusion:** shared primitives should cover token/phrase detection, but scoring functions remain distinct because of input format + scale.

3. **Fallback & safety signals overlap.**
   - Both pipelines check for `fallback`, `rollback`, `oversight`, and risk language.
   - Evaluator currently duplicates regex literals; candidate to consume shared pattern lists from `ocers_rules` once stabilised (S2 task candidate).

4. **Receipts/tests rely on deterministic pattern sets.**
   - Validator goldens (`tests/test_brief.py`) ensure ensemble output is stable per text sample.
   - Evaluator tests (`tests/test_ocers_eval.py`) cover structured examples. No cross-tests exist to ensure shared primitives stay in sync.
   - **Observation:** after moving helpers into `ocers_rules`, we should introduce explicit unit tests that exercise the shared API directly (planned under S3).

## Next steps
- Wire evaluator to shared helpers where safe (start with normalization/pattern utilities) without breaking headed-section logic.
- Introduce regression tests around `ocers_rules` to lock the heuristics before further refactors.
- Track any scoring drift once evaluator leans on shared primitives; update documentation/goldens accordingly.
