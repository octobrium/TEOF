# Legacy Artifact Cold Storage Summary (2025-11-09)

- CLI: `python3 -m tools.artifacts.cold_storage snapshot --source artifacts/builds --out artifacts/cold_storage/<ts>`
- Guard: `scripts/ci/check_legacy_cold_storage.py`
- Tests: `tests/test_cold_storage.py`

Snapshot stats:

| Bundle | Files | Bytes | Notes |
| --- | --- | --- | --- |
| `legacy-2025-11-09T051500Z` | 412 | 78 MB | Includes historic `_report/usage/*` |

This tracked receipt replaces the `_report/agent/...` requirement file referenced by the plan.
