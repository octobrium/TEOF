# ND-063 Receipts Index Streaming Requirements (2025-11-09T05:45Z)

- Produce incremental shards (e.g., 500 entries) with hash chaining + manifest.
- CLI `python -m tools.autonomy.receipts_index stream --dest ...` generating `_report/usage/receipts-index/stream/*.jsonl`.
- Consumers read pointer `_report/usage/receipts-index-latest.jsonl`.
