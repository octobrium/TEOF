# Agent Proposal Justification — 2025-09-19-tooling-prune

## Why this helps
Automation helpers and bus CLIs shipped during the macro hygiene sprint overlap and drift quickly. Several commands broadcast inconsistent flags, while dormant helpers still live under `tools/agent/` and confuse new sessions. Pruning and hardening the tooling reduces operational drag and ensures surviving commands stay trustworthy.

## Proposed change
- Audit `tools/agent/`, supporting scripts, and docs to map active usage vs. stale helpers.
- Archive or remove unused automation tooling, relocating it into `_apoptosis/<stamp>/` with notes.
- Normalize CLI UX (flag names, help text, docs) for the maintained commands and align the bus helpers.
- Add lightweight smoke/regression coverage so future tool drift is caught automatically.

## Receipts to collect
- `_report/agent/codex-3/tooling-prune/notes.md`
- `_report/agent/codex-3/tooling-prune/actions.json`
- `_report/agent/codex-3/tooling-prune/tests.json`
- Updated docs or helper modules referenced in the plan

## Tests / verification
- `pytest tools/tests/test_agent_cli.py`
- `python3 tools/maintenance/prune_artifacts.py --dry-run` (to confirm apoptosis relocation flows)

## Ethics & safety notes
Ensure pruned helpers either move into `_apoptosis/` or are documented before deletion. Keep bus CLI interfaces backwards compatible or document required migration steps.
