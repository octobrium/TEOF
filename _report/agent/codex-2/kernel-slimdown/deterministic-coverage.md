# Kernel Slimdown — Deterministic Coverage (S3)

## Updates
- Added `tests/test_ocers_rules.py` to lock shared heuristic behaviour (`norm_text`, `contains_any`, and the OCERS judgement outputs).
- Captured deterministic receipts via runner: `_report/runner/20250918T221405Z-20155a7c.json` (pytest covering shared heuristics + validator/evaluator smoke).
- Verified existing ensemble goldens remain stable through `tests/test_brief.py`.

## Result
Shared heuristics now have unit coverage and receipts, ready for checkpoint sign-off once additional golden updates are deemed unnecessary.
