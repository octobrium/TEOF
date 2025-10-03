# Relay Insight Sprint Case Study

> **Status:** Published (receipts anchored below)

## Summary
- **Client:** relay-pilot (anonymised)
- **Objective:** deliver a cite-backed strategy brief in 48 hours.
- **Guardrails:** diff limit 200, required test `pytest`, receipts under
  `_report/usage/case-study/relay-insight/`.
- **Summary receipt:** `_report/usage/case-study/relay-insight/summary.json`
- **Public asset:** [`docs/impact/relay-insight-public.md`](relay-insight-public.md)
- **Impact ledger entry:** see `docs/vision/impact-ledger.md` (2025-10-03)
- **Status:** Published; all receipts and ledger updates captured.

### Sprint Snapshot
- `conductor-run-20251003T191500Z.json` records the live autonomy cycle and references command/test receipts.
- `command-log-20251003T191500Z.json` lists executed steps (`make quickstart-check`, `pytest tests/test_case_study_summary.py -q`).
- `tests-20251003T191310Z.json` captures the pytest receipt for the case-study summariser guard.
- `diffs-20251003T191620Z.json` enumerates the plan/doc deltas tied to this sprint.

## Baseline (Before)
- Authenticity status: `_report/usage/external-authenticity.json`
- Objectives snapshot: `_report/usage/objectives-status.json`
- Decision intake: `memory/decisions/decision-20250926T220511Z.json`

## Intervention (During)
| Artifact | Path |
| --- | --- |
| Consent notes | `_report/usage/case-study/relay-insight/consent.json` |
| Conductor dry run | `_report/usage/case-study/relay-insight/conductor-dry-run-20250927T195724Z.json` |
| Command log | `_report/usage/case-study/relay-insight/command-log-20251003T191500Z.json` |
| Diff/test receipts | `_report/usage/case-study/relay-insight/tests-20251003T191310Z.json`, `_report/usage/case-study/relay-insight/diffs-20251003T191620Z.json` |
| Live run summary | `_report/usage/case-study/relay-insight/conductor-run-20251003T191500Z.json` |

## Results (After)
- Impact entry: `memory/impact/log.jsonl` (2025-10-03T19:26:30Z)
- Public asset: [`docs/impact/relay-insight-public.md`](relay-insight-public.md)
- Authenticity delta: see `_report/usage/external-authenticity.json` (post-run snapshot)

### Findings
- Quickstart receipts (`_report/usage/onboarding/build-20251003T190822Z.json`, `_report/usage/onboarding/quickstart-20251003T190832Z.json`) confirm install + `teof brief` success in under ten minutes, satisfying the onboarding gate before external delivery.
- Case-study summariser pytest receipt (`tests-20251003T191310Z.json`) now travels with the sprint, reducing manual audit overhead.
- Diff receipt (`diffs-20251003T191620Z.json`) ties narrative and plan edits together for reproducibility, mirrored in the public brief and impact ledger entry.

## Verification Checklist
- [x] All receipts stored under `_report/usage/case-study/relay-insight/`
- [x] Impact logged in `docs/vision/impact-ledger.md`
- [x] Case study published with links to receipts
- [x] `python -m tools.impact.case_study summarize --slug relay-insight --out _report/usage/case-study/relay-insight/summary.json` run after live sprint
- [x] External asset linked & authenticity delta captured

## Next Steps
1. Maintain the public asset if follow-on sprints introduce new receipts.
2. Refresh the case-study summary via `python -m tools.impact.case_study summarize --slug relay-insight --out _report/usage/case-study/relay-insight/summary.json` after any updates.
3. Extend the ledger entry if commercial outcomes accrue (e.g., paid renewal).
