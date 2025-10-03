# Session Guard Upgrade Design (2025-10-03)

## Objectives
- Ensure `session_boot` refuses to run when the active manifest agent differs from `--agent` (or defaults) unless explicitly overridden.
- Verify the current branch matches `agent/<agent_id>/...` (or is main/release) to prevent cross-seat edits.
- Provide opt-out flags (`--allow-manifest-mismatch`, `--allow-branch-mismatch`) for rare scenarios while logging a warning receipt.

## Implementation sketch
1. Add `_ensure_manifest_agent(agent_id, allow=False)` that reads `AGENT_MANIFEST.json` and raises `SystemExit` with guidance when mismatch occurs. Accept `--allow-manifest-mismatch` to downgrade to warning.
2. Capture branch via `git rev-parse --abbrev-ref HEAD`; ensure prefix `agent/{agent_id}/` or allowed branches set {"main", "origin/main"}. Failure raises with resolution instructions unless `--allow-branch-mismatch` flag is passed.
3. When overrides used, append note to `_report/agent/<id>/session_guard/warnings.jsonl` for audit.
4. Update argparse to include the new boolean flags and integrate checks before sync.
5. Extend tests (`tests/test_session_boot.py`) with harness using monkeypatched manifest/branch states to cover success, failure, and override cases.
6. Document guardrails in `docs/parallel-codex.md` (Session Loop + Manifest discipline sections) and broadcast via `manager-report`.

## Open questions
- Should `session_boot` auto-activate manifest variant? For now, keep manual to avoid unintended swaps; guidance stresses running manifest_helper first.
- Branch check should allow `HEAD` detached? Proposed: treat detached HEAD as mismatch unless override flag provided.
