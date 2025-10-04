# TEOF Quick Reference (Draft)

Use this sheet to answer common questions without re-scanning the entire corpus.
Each entry points to authoritative documents.

## Alignment Foundations
- **Ethical Baseline:** `docs/foundation/alignment-protocol/tap.md#iii-service-to-the-observer`
- **Commandments:** `docs/commandments.md`
- **Workflow order:** `docs/workflow.md#teof-master-workflow-minimal-v13`

## Defensive Procedure
- **Observation → escalation → receipts clause:** `docs/foundation/alignment-protocol/tap.md#iii-service-to-the-observer`
- **Defensive logging:** `docs/commandments.md#defensive-exceptions`, `docs/workflow.md` (Defensive exception logging)

## Automation Helpers
- Onboarding: `bin/teof-up`
- Scenario logging: `python3 -m tools.ethics.log_scenario`
- Receipts status: `python3 -m tools.receipts.main status`

## Philosophy Guidance
- **Meaning/purpose:** `docs/foundation/alignment-protocol/tap.md#meaning`, `docs/whitepaper.md#purpose`
- **Other minds / trust:** `docs/foundation/alignment-protocol/tap.md#observer`, `docs/workflow.md#observation-primacy`
- **Prompt module:** `python3 -m tools.prompts.philosophy "<question>"` → writes `_report/usage/prompts/philosophy-<UTC>.md`

Add new rows as the philosophical alignment plan delivers richer mappings.
