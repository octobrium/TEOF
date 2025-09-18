# Manifest Helper Survey — 2025-09-18

- Existing manifests: AGENT_MANIFEST.json (active), AGENT_MANIFEST.codex-4.json, AGENT_MANIFEST.codex-manager.json, etc. No helper to swap.
- Auto-claim changes rely on correct manifest identity. Manual `cp` risks losing notes.
- Helper should backup current manifest, swap to target, and optionally restore default.
- Need to ensure CI/automation can verify via receipts (e.g., `_report/agent/.../manifest-switch.json`).
