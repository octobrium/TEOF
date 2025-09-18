# Plan Justification — 2025-09-19-governance-trim

## Why this matters
Agent onboarding now spans `.github/AGENT_ONBOARDING.md`, `docs/AGENTS.md`, `docs/parallel-codex.md`, and scattered governance notes. Each surface repeats the quick loop, coordination bus rules, and cadence expectations with diverging wording. The drift inflates review time, makes updates error-prone, and obscures which instructions are canonical—risking conflicts with governance policy.

## Proposal
1. Audit the current guidance set and decide which doc owns each concept (quickstart, coordination, governance escalations).
2. Reshape `.github/AGENT_ONBOARDING.md` into a lean entry point that links to the authoritative doc for deeper detail.
3. Adjust `docs/AGENTS.md`, `docs/parallel-codex.md`, and related governance references so they complement (not duplicate) onboarding, including explicit links back to policy anchors.
4. Capture a delta report summarising the removals and new link structure for traceability.

## Deliverables
- Updated onboarding/governance docs with deduplicated content and clear cross-links.
- Delta report under `_report/agent/codex-4/apoptosis-003/` describing changes and rationale.
- Recorded receipts for doc edits and verification commands.

## Tests / verification
- Markdown lint within existing CI guardrails.
- Manual spot-check: follow the new onboarding path end-to-end to confirm links resolve and required governance sections remain accessible.

## Safety
Documentation-only changes; no automation or external calls. All removals remain recoverable via git history and receipts.
