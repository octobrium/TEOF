# Legacy Artifact Cold Storage

Retire historical automation artifacts (legacy conductor runs, old `_report/` bundles, `_apoptosis/` remnants) into compressed, hashed snapshots so the repo stays light while receipts remain auditable.

## Objectives

1. **Integrity** — every snapshot carries SHA-256 hashes per file plus an aggregate bundle hash.
2. **Traceability** — manifests cite source directories, plan IDs, receipts, and git commit so auditors can reconstruct provenance.
3. **Reversibility** — restoring a snapshot recreates the original directory tree with receipt hashes verified.
4. **Automation-friendly** — CLI emits machine-readable receipts, and CI guards enforce freshness plus the absence of stray raw artifacts.

## Snapshot format

| Field | Description |
| --- | --- |
| Bundle path | `artifacts/legacy_cold_storage/<snapshot_id>/bundle.tar.zst` (zstd level 10). |
| Manifest | `artifacts/legacy_cold_storage/<snapshot_id>/manifest.json` containing metadata table below. |
| Checksums | `artifacts/legacy_cold_storage/<snapshot_id>/SHASUMS.txt` with `<sha256> <relative_path>` per file. |

### Manifest schema

```json
{
  "snapshot_id": "legacy-2025-11-09T062200Z",
  "created_at": "2025-11-09T06:22:00Z",
  "git_commit": "abc1234",
  "source": [
    "_report/legacy_loop_out/2025-09-23",
    "_apoptosis/2025-09-30T010000Z"
  ],
  "files": 412,
  "bytes": 18743540,
  "bundle_sha256": "7d2f…",
  "hashes": {
    "_report/legacy_loop_out/2025-09-23/summary.json": "cf1c…",
    "…": "…"
  },
  "receipts": [
    "_report/usage/legacy-cold-storage/bundle-2025-11-09T062200Z.json"
  ],
  "notes": "Backfilled relay insight pilot history"
}
```

## CLI surface

```
python -m tools.artifacts.cold_storage snapshot \
  --source _report/legacy_loop_out/2025-09-23 \
  --source _apoptosis/2025-09-30T010000Z \
  --out artifacts/legacy_cold_storage \
  --receipt _report/usage/legacy-cold-storage \
  --notes "Backfilled relay insight pilot"

python -m tools.artifacts.cold_storage restore \
  --bundle artifacts/legacy_cold_storage/legacy-2025-11-09T062200Z/bundle.tar.zst \
  --dest scratch/legacy_restore

python -m tools.artifacts.cold_storage guard \
  --source _report/legacy_loop_out \
  --source _apoptosis \
  --max-raw 0 \
  --max-age-days 7
```

### Snapshot command behaviour

1. Validates that each `--source` path exists and is not already bundled.
2. Streams files into a tar archive while computing per-file SHA-256 hashes (no temp copies).
3. Writes `manifest.json`, `SHASUMS.txt`, and `bundle.tar.zst` to a new snapshot directory.
4. Emits a receipt (`_report/usage/legacy-cold-storage/bundle-<stamp>.json`) mirroring manifest metadata plus the pointer to the bundle.
5. Updates `_report/usage/legacy-cold-storage/latest.json` and appends to `history.jsonl`.
6. Deletes the original source directories unless `--keep-source` is supplied.

### Restore command behaviour

1. Verifies `bundle_sha256` from `manifest.json` before extraction.
2. Recreates the original directory structure under `--dest`.
3. Recomputes hashes and warns when mismatches appear.

## Receipts

- `_report/usage/legacy-cold-storage/bundle-<stamp>.json` — immutable receipt for each snapshot.
- `_report/usage/legacy-cold-storage/latest.json` — pointer the guard + dashboards read for the newest bundle.
- `_report/usage/legacy-cold-storage/history.jsonl` — append-only pointer history for automation sweeps.

## CI guard

`scripts/ci/check_legacy_cold_storage.py` runs `python -m tools.artifacts.cold_storage guard` and:

1. Fails when `_report/legacy_loop_out/` or `_apoptosis/` contains more than `LEGACY_COLD_STORAGE_MAX_RAW` raw directories (default `0`).
2. Verifies `_report/usage/legacy-cold-storage/latest.json` points to an on-disk bundle/manifest pair whose hash matches `bundle_sha256`.
3. Enforces freshness via `LEGACY_COLD_STORAGE_MAX_AGE_DAYS` (default `7`).

Environment knobs:

- `LEGACY_COLD_STORAGE_MAX_RAW` — maximum allowed raw directories per source before CI fails.
- `LEGACY_COLD_STORAGE_MAX_AGE_DAYS` — maximum permissible age (in days) for `latest.json`.

## Rollout

1. Backfill existing legacy directories by running `cold_storage snapshot` per backlog entry.
2. Update documentation and automation to consume `_report/usage/legacy-cold-storage/latest.json`.
3. Enable the CI guard once the initial backfill succeeds.

This specification satisfies plan step **S2** by defining the snapshot format, manifests, CLI requirements, receipts, and guard strategy for ND-064.
