# Design log — session_brief operator preset (2025-09-21)

## Goals
- Provide a `--preset operator` so `session_brief` walks the Operator Mode checklist from `docs/AGENTS.md`.
- Emit deterministic receipts verifying prerequisites: manager-report tail, plan validation, quickstart receipts, claim seed/task sync, and Meta-TEP pointer when present.
- Keep default behaviour unchanged; preset only adds structured checklist output.

## Outline
- Extend CLI parser with `--preset` choices (`operator`, maybe `minimal` placeholder). Operator preset triggers additional checks and summary formatting.
- Checklist structure: list of steps with `title`, `status` (`pass|fail|warn`), `details`, and `remediation`. Map to JSON output plus console summary.
- Checks to implement initially:
  1. Manager-report tail receipt exists at `_report/session/<agent>/manager-report-tail.txt`.
  2. Plans validate (`python3 tools/planner/validate.py --strict`). Optionally capture summary path when present.
  3. Quickstart receipts present (`artifacts/ocers_out/latest/brief.json`) or mark warn when missing.
  4. Claim seed exists for active plan (scan `_bus/claims/**`).
  5. Task sync receipts in `_report/agent/<id>/task_sync/` (warn when missing).
  6. Meta-TEP pointer: if `docs/proposals/` has open draft referencing manager-report entry, report status.
- Each check returns dict with boolean + context string; aggregator prints table and writes JSON receipt under `_report/agent/<id>/session_brief/<timestamp>-operator.json`.

## Implementation notes
- Factor checklist definitions into `CHECKS` list of callables; pass `root` and `agent_id`.
- Provide `--output` override for deterministic file path (used in tests).
- Ensure new directories use `mkdir(parents=True, exist_ok=True)` and respect git tracked requirements by writing JSON.
- Update docs (`docs/automation.md`, `docs/parallel-codex.md`, quick-links) after implementation.

## Testing
- New pytest covering success and missing receipt scenario using tmp repo (git init) to satisfy tracked guard.
- Existing session_brief tests should continue to pass; add coverage for new CLI options.
