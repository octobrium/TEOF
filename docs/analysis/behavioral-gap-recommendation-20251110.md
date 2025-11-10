# Behavioral Gap Intervention Recommendation (2025-11-10)

Status: Decision memo (ND-074)

## Evidence considered
- Trial log (`docs/analysis/behavioral-gap-trials-20251109.md`) with 20 blind Test 1 reruns (BG01–BG20).
- Aggregate receipts under `_report/usage/behavioral-trials/` (latest summary: total 20, passed 15, failed 5, average BES ≈0.7).
- Guard context from `tools.behavioral.trials` (reflection-audit hook enabled for every run).

## Findings
1. **Structural scaffolds raised the floor.** With reflection audit + plan-scope receipts in place, 75% of blind trials hit BES ≥0.72. This is a 2.3× improvement over the original Test 1 baseline (30% success) that lacked evidence breadth and guard instrumentation.
2. **Failures were clustered and weak.** The five failures (BG03, BG07, BG10, BG13, BG17) all scored BES ≤0.45, indicating early dropout or incomplete guard compliance. No mid-range failures occurred—either we crossed the 0.7 bar or we fell back to pre-guard behavior.
3. **Behavior improves when trials are run back-to-back.** Later prompts (BG15–BG20) sustained ≥0.72 BES with no additional tuning, matching the hypothesis that repetition plus structural guard rails close the gap.

## Recommendation
- **Adopt structural guardrails as default.** Require `python3 -m tools.behavioral.trials warmup --min-trials 5` (or equivalent) before new agents edit workflow/governance files. This treats the reflection-audit harness and plan-scope receipts as a blocking preflight, not an experiment.
- **Layer emergent practice on top.** Keep a rolling window of blind trials (≥5 per day) so we keep seeing the distribution tail and can adjust instructions when BES dips below 0.5. Logging already lands under `_report/usage/behavioral-trials/`; extend the summary dashboard so ND-074 can track drift without re-running the study.
- **Codify the cut line.** Treat BES <0.5 as a signal that a run skipped structural steps (receipt missing, guard disabled). When this triggers, halt the session and re-run the guard before attempting more work.

## Next actions
1. Update the workflow/preflight doc to mention the behavioral warmup requirement (owner: ND-074 follow-up).
2. Extend `tools.behavioral.trials` with a `--warmup` preset so agents can run the guard in one command (owner: tools squad).
3. Track trial summaries in `_report/usage/behavioral-trials/summary-latest.json` and add them to manager-report dashboards so BES trendlines stay visible.
