# Plan Justification — 2025-09-18-manifest-helper-codex3

## Problem
Agent manifest swapping (multiple codex sessions) is still manual; manager reports mention env hygiene. Without a helper, agents risk stomping manifests or forgetting to restore defaults when switching roles.

## Proposed change
Build a helper (likely `tools/agent/manifest_helper.py` or similar) to:
- List available manifest variants (e.g., `AGENT_MANIFEST.codex-*.json`).
- Swap the active `AGENT_MANIFEST.json` to a chosen variant and optionally restore a default.
- Provide a safe backup and receipts so automation can verify switches.

CLI should support `--list`, `--activate <name>`, `--restore-default`. Include docs in `docs/agents.md`/`docs/parallel-codex.md` for multi-agent workflows.

## Receipts
- `_report/agent/codex-3/manifest-helper/pytest.json`
- `_report/agent/codex-3/manifest-helper/notes.md`

## Tests / verification
- New tests covering listing and switching manifest files (tmpdir-based).

## Safety
Operates within repo; ensures backups before overwriting. Default dry-run/list mode to avoid accidental swaps.
