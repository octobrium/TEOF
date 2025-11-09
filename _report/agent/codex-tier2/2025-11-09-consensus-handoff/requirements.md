# Consensus Handoff Requirements — 2025-11-09

- Capture situations where an agent cannot reach the bus or push guard due to sandbox/network constraints.
- Receipt must preserve pending action, branch/plan references, and explicit next steps so another seat can continue without tribal knowledge.
- Aligns with the coordination deadlock finding documented in `memory/impact/coordination-deadlock-finding-20251109.md` and new workflow guidance under "Coordination Deadlock Resolution".
- Output lives under `_report/analysis/consensus-handoff/` with a stable `latest.json` pointer for CI/guards to inspect later.
