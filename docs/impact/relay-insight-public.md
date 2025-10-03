# Relay Insight Sprint — Public Summary

**Date:** 2025-10-03  
**Partner:** relay-pilot (anonymised)  
**Objective:** deliver a cite-backed strategy brief inside 48 hours while keeping every step auditable.

---

## Why it matters
- Relay partners demand deterministic guardrails before adopting the API-driven research loop. This sprint demonstrates the full chain: consent, automation prompts, guarded commands, and post-run receipts.
- Quickstart onboarding was re-run in a clean environment so new collaborators can reproduce the install + `teof brief` smoke in under ten minutes.

## What we did (with receipts)
1. **Consent & scope** — `_report/usage/case-study/relay-insight/consent.json`.
2. **Autonomy conductor** — dry-run prompt (`.../conductor-dry-run-20250927T195724Z.json`) and live execution (`.../conductor-run-20251003T191500Z.json`).
3. **Guarded commands** — `make quickstart-check` + `pytest tests/test_case_study_summary.py -q` captured in
   `_report/usage/case-study/relay-insight/command-log-20251003T191500Z.json` and the pytest receipt `tests-20251003T191310Z.json`.
4. **Change surface** — git diff summary `_report/usage/case-study/relay-insight/diffs-20251003T191620Z.json` ties narrative + plan edits to recorded hashes.
5. **Roll-up summary** — `_report/usage/case-study/relay-insight/summary.json` tracks present/missing artifacts for downstream audits.

## Outcomes
- Cite-backed strategy brief delivered within SLA; partner confirmed the insights unlocked two follow-up scoping conversations.
- Automation guardrails (diff limits, pytest receipts) remained satisfied; no manual overrides required.
- Relay Insight offering (Plan `2025-09-24-relay-offering`) promoted to *done* with reproducible receipts, unblocking ND-016 publication.

## Verify it yourself
```bash
python3 -m tools.impact.case_study summarize --slug relay-insight \
  --out _report/usage/case-study/relay-insight/summary.json
```
Inspect the receipts listed above to replay the sprint end-to-end.
