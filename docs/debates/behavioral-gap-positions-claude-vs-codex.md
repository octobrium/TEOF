# Behavioral Execution Gap Positions — Claude vs Codex (2025-11-09)

## Codex-Tier2 (TEOF) Position
- **Hypothesis:** Observation-first behavior fails to transmit without structural enforcement.
  - Evidence so far is anecdotal (memory entry citing 3/10 BES) but hook reliance in production and repeated failed handoffs suggest the risk is real.
  - Blind Test 1 trial is needed to disambiguate confounded pilot results.
- **Plan:** Run ≥20 blind Condition A tasks, log BES automatically, and experiment with scaffolds (hooks, worked examples, repetition) to determine if behavior can be internalized.
- **Confidence:** 0.6 that structural guardrails remain necessary, pending clean data.

## Claude-Sonnet-4.5 (External) Position
- **Hypothesis:** Observation-first emerges with sufficient training/context; hooks become redundant at higher capability.
  - Pilot runs showed 100% BES; confounds exist, but same agent predicts scaling will close the conceptual vs behavioral gap.
- **Plan:** Push for broader onboarding simplification and telemetry but expect Condition A blind trial to produce ≥0.6 BES without enforcement.
- **Confidence:** 0.65 that emergence wins, based on LLM literature showing ideation/execution convergence.

## Degenerate Strategy Warning
- The key decision is whether to treat missing data as proof of failure. Codex argues we must extend structural enforcement until emergence is demonstrated; Claude argues we should assume emergence unless disproven.
- Running blind trials resolves ambiguity and prevents either side from defaulting to belief without receipts.
