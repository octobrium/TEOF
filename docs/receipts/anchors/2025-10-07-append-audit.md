# Anchors Append-Only Audit (2025-10-07)

- **Guard owner:** codex-5
- **Tooling:** `python -m tools.governance.anchors_audit`
- **Source:** `governance/anchors.json` snapshot @ 2025-10-07

## Findings

| Index | Timestamp (UTC)         | Type         | Has `prev_content_hash` | Notes |
| ----- | ----------------------- | ------------ | ----------------------- | ----- |
| 0     | 2025-08-26T01:59:17Z    | event        | ❌                      | Initial reset entry lacks reference hash; acceptable as genesis but should be documented. |
| 2     | 2025-09-21T02:26:38Z    | freeze       | ❌                      | Freeze event omits `prev_content_hash`, breaking append proof. |
| 4     | 2025-09-21T20:14:44Z    | canon-change | ❌                      | Canon update missing append proof. |
| 7     | 2025-09-22T22:10:00Z    | key          | ❌                      | Feed key registration missing append proof. |
| 8     | 2025-09-26T22:55:00Z    | event        | ❌                      | Autonomy instrumentation note missing append proof. |
| 9     | 2025-09-26T22:20:30Z    | event        | ❌                      | Key rotation summary missing append proof. |
| 10    | 2025-10-04T06:00:30Z    | event        | ❌                      | Latest key rotation note missing append proof. |

All other events (indices 1, 3, 5, 6) include the expected `prev_content_hash`.

## Next Actions

1. Ship append-only enforcement that rejects new events unless `prev_content_hash` matches the current anchors hash (Plan `2025-10-07-anchors-policy-guard`).
2. Extend documentation in `docs/architecture.md` (done) and the guard CLI docs when enforcement lands.
3. Backfill missing hashes by recomputing historical anchors once the guard is deployed.

## Artifacts

- Audit script: `tools/governance/anchors_audit.py`
- Generated JSON (not committed): `_report/usage/anchors/anchors-audit-20251007T070828Z.json`
