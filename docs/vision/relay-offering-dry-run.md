# Relay Insight Sprint — Dry-Run Checklist (2025-09-26)

This walkthrough captures the assets created during the 2025-09-26 dry run of
the Relay Insight Sprint. Use it as the default playbook before onboarding a
paying client.

## 1. Capture the decision request
```bash
python3 -m tools.autonomy.decision_intake \
  --title "Relay Insight Sprint pilot scope" \
  --objective "Validate onboarding + guardrails for first paid client" \
  --constraints "diff<=200,pytest" \
  --success-metric "Pilot brief delivered within 48h with audit receipts" \
  --reference docs/vision/relay-offering-collateral.md \
  --reference docs/vision/relay-offering-dry-run.md \
  --plan-id 2025-09-24-relay-offering
```
- Receipt: `memory/decisions/decision-20250926T220511Z.json`
- Outcome: structured intake ready for conductor + relay prompts.

## 2. Snapshot objective guardrails
```bash
python3 -m tools.autonomy.objectives_status --window-days 7 \
  --out _report/usage/objectives-status.json
```
- Confirms L2 objectives coverage (reflections, autonomy cadence, guardrail
  integrity, external sensing).
- Highlights gaps (currently O3 coordination receipts) to resolve before
  accepting payment.

## 3. Generate a guarded prompt (dry run)
```bash
python3 -m tools.autonomy.conductor \
  --plan-id ND-014 \
  --diff-limit 200 \
  --test pytest \
  --receipts-dir _report/usage/autonomy-conductor \
  --dry-run \
  --emit-prompt \
  --emit-json
```
- Produces `conductor-<timestamp>.json` with guardrails + objectives snapshot.
- Leaves ND-014 in `pending` so a human can run the sprint or requeue.
- If ND-014 is not pending the conductor exits cleanly; reset the status in
  `_plans/next-development.todo.json` before attempting a live run.

## 4. Update impact + collateral receipts
- Append sprint instrumentation to `memory/impact/log.jsonl`.
- Summarise guardrail-enabled monetization path in
  `docs/vision/impact-ledger.md`.
- Share collateral kit: `docs/vision/relay-offering-collateral.md`.

## Next steps before live client
1. Resolve O3 coordination dashboard freshness (record a new dashboard receipt).
2. Draft sample brief using conductor prompt output; attach to collateral.
3. Publish landing page + intake form link referenced above.
4. Tag the intake decision in `_bus/claims/ND-014.json` once pilot is scheduled.
