# Capability Heartbeat Receipts

Purpose: keep a public, git-tracked proof that the critical TEOF CLIs still run,
even when `_report/` is gitignored. This directory mirrors the receipts produced
by the automation guardrails so capability inventory checks can cite stable
artifacts.

## Layout

- `plan-scope-*.json` — output from `python3 -m teof plan_scope ...` showing the
  clean working tree and manifest at the moment the capability sweep ran.
- `receipts_stream-*.json` — receipts index run proving `_report/usage/...`
  shards are up-to-date.
- `receipts_stream_guard-*.json` — guard receipts from
  `python3 -m teof receipts_stream_guard ...` so CI can prove the pointer was
  rehashed.
- `scan_history-*.json` — `python3 -m teof scan_history` receipts (usually
  limited to the latest entry) so operators can prove the history CLI still
  emits data.
- `latest.json` — pointer to the most recent plan-scope receipt so downstream
  docs (and humans) can jump directly to the newest sweep.

## Update Workflow

1. **Plan scope sweep**
   ```bash
   python3 -m teof plan_scope \
     --plan 2025-11-09-plan-scope \
     --manifest _plan_scope/manifests/plan-scope.json \
     --out docs/usage/plan-scope \
     --receipt-dir docs/usage/capability-heartbeat
   ```
   This emits `plan-scope-<plan>-<ts>.json` plus updates `latest.json`.

2. **Receipts index + guard**
   ```bash
   python3 -m teof receipts_stream \
     --dest _report/usage/receipts-index/stream \
     --pointer _report/usage/receipts-index/latest.json \
     --receipt docs/usage/capability-heartbeat/receipts_stream-<ts>.json

   python3 -m teof receipts_stream_guard \
     --pointer _report/usage/receipts-index/latest.json \
     --receipt docs/usage/capability-heartbeat/receipts_stream_guard-<ts>.json
   ```

3. **Scan history receipt**
   ```bash
   python3 -m teof scan_history --limit 1 \
     --receipt-path docs/usage/capability-heartbeat/scan_history-<ts>.json
   ```

Keep the filenames timestamped (UTC, ISO-ish) and refresh `latest.json` after
each run so capability inventory reports can cite the most recent evidence.
