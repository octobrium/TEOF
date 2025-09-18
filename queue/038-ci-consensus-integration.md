# Task: Integrate consensus tooling into CI
Goal: run the new consensus ledger/receipts/dashboard checks in CI so regressions surface automatically.
Notes: update guardrails workflow(s) to execute the CLIs, capture receipts, and fail on missing artifacts.
OCERS Target: Evidence↑ Safety↑
Sunset: revisit after the next capsule freeze once consensus tooling stabilizes.
Fallback: rely on manual pytest runs before merging consensus work.
