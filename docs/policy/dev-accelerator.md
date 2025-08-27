# TEOF Development Accelerator (TDA)
Goal: maximize OCERS delta per unit time with bounded risk (Kelly-style).

Loop:
1) Observe: collect tasks in `queue/*.md` (each with Goal, Scope, OCERS target, Sunset/Fallback).
2) Generate: proposer agent(s) writes a patch idea (dry-run) → `_report/autocollab/<ts>/…`.
3) Evaluate: critic agent(s) score proposal with OCERS and risk notes; attach receipts.
4) Select: accept small fraction f of proposals into a sandbox branch **only after** human review.
5) Learn: log OCERS deltas and acceptance; adjust f (risk budget) per Kelly estimator.

Risk budget (intuition): start f≈0.1. Increase only when win-rate × payoff > loss-rate / harm.
Everything remains optional until receipts justify promotion.
