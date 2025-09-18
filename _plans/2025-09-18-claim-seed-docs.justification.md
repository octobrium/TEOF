# Agent Proposal Justification — 2025-09-18-claim-seed-docs

## Why this helps
Now that claim seeding exists, agents need canonical instructions. Documenting the helper in docs/workflow + agent onboarding reduces repeated orientation and encourages pre-seeded vacancies for faster self-organization.

## Proposed change
Codex-2 will document the claim seeding workflow, add examples to docs/AGENTS.md and docs/workflow.md, and drop a short HOWTO in docs/maintenance/ or tools README as appropriate. No code changes expected beyond docs.

## Receipts to collect
- `_report/agent/codex-2/claim-seed-docs/notes.md`

## Tests / verification
- `python -m tools.agent.session_brief` (ensure instructions reference the command)
- `python3 tools/planner/validate.py`

## Ethics & safety notes
Docs only.
