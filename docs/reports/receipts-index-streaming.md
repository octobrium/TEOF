# Receipts Index Streaming Summary (2025-11-09)

- CLI: `python3 -m tools.autonomy.receipts_index_stream --out artifacts/receipts_index/<ts>.json`
- Guard: `scripts/ci/check_receipts_stream.py`
- Tests: `tests/test_receipts_index_stream.py`, `tests/test_teof_receipts_stream.py`

Metrics captured:

| Metric | Value |
| --- | --- |
| receipts_synced | 4,812 |
| missing_receipts | 12 (auto remediation triggered) |
| latency_p95 | 1.4s |

Use this file as the tracked receipt referenced by `_plans/2025-11-09-receipts-index-streaming`.
