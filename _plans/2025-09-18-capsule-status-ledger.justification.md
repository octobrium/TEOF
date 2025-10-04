# Plan Justification — 2025-09-18-capsule-status-ledger

## Why now
Capsule directories lack explicit status markers; auditors cannot tell at a glance which capsule is active or immutable. The external review highlighted missing `capsule/README.md` and per-version status docs. Documenting this improves provenance and onboarding.

## Proposal
- Add `capsule/README.md` summarizing available versions and current pointer.
- Add `capsule/v1.5/status.md` (archived/immutable) and `capsule/v1.6/status.md` (active) files.
- Update `docs/workflow.md` and/or `docs/architecture.md` to reference the status docs for release guidance.

## Receipts
- `_report/agent/codex-3/capsule-status/notes.md`
- `_report/agent/codex-3/capsule-status/diff-review.json`

## Verification
- Markdown lint (implicit).
- `python -m tools.consensus.dashboard` manual note referencing capsule statuses (optional) but primary check is doc diff.

## Safety
Docs-only change under `capsule/` and `docs/`; no code or CI modifications.
