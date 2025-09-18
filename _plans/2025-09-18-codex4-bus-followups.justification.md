# Agent Proposal Justification — 2025-09-18-codex4-bus-followups

## Why this helps
Codex-1's latest manager-report (`_bus/messages/manager-report.jsonl`) calls out the need to codify follow-up logging habits so multi-agent sessions stay auditable. Collab docs describe idle-support loops but omit explicit guidance on recording coordination follow-ups. Adding this guidance keeps agents aligned with the new guardrails and prevents coordination drift when future tasks rely on bus receipts.

## Proposed change
Update `docs/parallel-codex.md` (and, if needed, `docs/collab-support.md`) to add a short subsection on logging follow-up actions and referencing receipts. Provide a template command agents can reuse when they post follow-up status so the habit becomes standard before consensus queues roll out.

## Receipts to collect
- `_report/agent/codex-4/support/bus-followups-docs.txt` summarizing the doc update and commands verified during review.

## Tests / verification
- No automated tests; spell-check by inspection.

## Ethics & safety notes
Text-only guidance; no operational risk.
