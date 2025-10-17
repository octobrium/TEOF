# Relay Insight Sprint — Sample Brief (Excerpt)

## Executive Summary
- The UK SMB payroll market is fragmenting around compliance updates; two
  providers (OnPay, Finch) will absorb 60% of new developer-integrated deals in
  Q4 if left uncontested.
- Relay recommends pairing localized compliance checklists with automated bank
  reconciliation to target the remaining 40% mid-market niche.
- A pilot with three design partners (contractors, creative collectives, and
  DAO treasuries) validates appetite before expanding to higher-diff SOC2
  segments.

## Signals Table
| Source | Timestamp (UTC) | Signal | retired observation loop Trait |
| --- | --- | --- | --- |
| `_report/external/sample/20250922T221000Z.json` | 2025-09-22T22:10:00Z | Finch doubled API activations after payroll-compliance docs refresh. | Observation |
| `docs/vision/power-levers.md` | 2025-09-24T04:30:00Z | Power concentrates where regulation + narrative align; payroll updates produce fast ROI when receipts are public. | Coherence |
| `artifacts/systemic_out/latest/brief.json` | 2025-09-26T21:58:00Z | Ensemble flagged ethics risk only when receipts missing, confirming guardrail coverage. | Ethics |

## Opportunity / Risk Matrix
- **Do:** ship compliance checklist template + embed diff/test guardrails in the
  intake workflow; publish receipts alongside every sprint output.
- **Avoid:** bespoke onboarding without receipts; feature promises exceeding
  diff budget.
- **Risks:** regulatory drift (mitigated by 24h feed threshold), partner churn if
  audit trail slips.

## Command Log Snapshot
- `python3 -m tools.autonomy.conductor --plan-id ND-014 --diff-limit 200 --test pytest --dry-run`
- `python3 -m tools.autonomy.objectives_status --window-days 7 --out _report/usage/objectives-status.json`
- `python3 -m tools.external.summary --out _report/usage/external-summary.json --disable-auth-alert`

## Next Steps
1. Convert this excerpt into a Notion deliverable with linked receipts.
2. Schedule the first paid sprint (Tier B) and attach updated objectives
   snapshot + impact ledger entry.
3. Run `teof-impact-log --title "Relay sprint client #1" ...` once the pilot is
   delivered.
