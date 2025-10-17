# TEOF Development Accelerator (TDA)
Goal: maximize systemic delta per unit time with bounded risk (Kelly-style).

Loop:
1) Observe: collect tasks in `queue/*.md` (each with Goal, Scope, systemic targets, Sunset/Fallback).
2) Generate: proposer agent(s) writes a patch idea (dry-run) → `_report/autocollab/<ts>/…`.
3) Evaluate: critic agent(s) score proposal with systemic axis coverage and risk notes; attach receipts.
4) Select: accept small fraction f of proposals into a sandbox branch **only after** human review.
5) Learn: log systemic deltas and acceptance; adjust f (risk budget) per Kelly estimator.

Risk budget (intuition): start f≈0.1. Increase only when win-rate × payoff > loss-rate / harm.
Everything remains optional until receipts justify promotion.
