# Apoptosis Snapshot Compression

Reduce `_apoptosis/` footprint by bundling retired receipts into hashed archives with reversible manifests and receipts.

## Current state

- Hygiene scripts copy entire `_report/**` slices into `_apoptosis/<stamp>/…`, leaving thousands of small files under git control.
- No metadata describes what ended up in each snapshot or how to restore it.
- CI cannot enforce that bundles exist because the directory may already contain the raw dumps.

## Target design

| Concern | Spec |
| --- | --- |
| Bundle artifact | `artifacts/apoptosis/<stamp>/bundle.tar.xz` (tar stream compressed with xz). |
| Contents | Original files (relative paths), plus `manifest.json` and `SHASUMS.txt`. |
| Manifest schema | ```json<br>{"bundle_id":"apo-20251109T061200Z","created_at":"2025-11-09T06:12:00Z","source_dir":"_apoptosis/2025-11-09/SESSION-123","git_commit":"abc1234","file_count":1845,"total_bytes":6231040,"hashes":{"bundle_sha256":"…","files":{"_report/...":"<sha256>",…}},"receipts":["_report/usage/prune/receipt-...json"],"notes":"<optional>"}<br>``` |
| Receipts | `_report/usage/apoptosis/bundles-<UTC>.json` summarises bundle metadata. The CLI appends a pointer file `_report/usage/apoptosis/latest.json`. |
| CLI | `python -m tools.autonomy.apoptosis_compress bundle <snapshot_dir>` bundles snapshots; `restore` and `verify` subcommands unpack/verify archives. |
| Hash chain | `SHASUMS.txt` contains `<sha256> <path>` for every file inside the bundle; bundle hash stored in manifest + receipt. |
| CI guard | `scripts/ci/check_apoptosis_bundles.py` ensures `_apoptosis/` contains only the newest raw dump (if any) and every bundle referenced in `_plans/` or receipts resolves to an artifact. |

## CLI behaviour

1. `bundle` command:
   - Validates `--source` exists and is not empty.
   - Streams files into a tarball, computing per-file checksums as it goes.
   - Writes `manifest.json`, `SHASUMS.txt`, and the compressed archive under `artifacts/apoptosis/<bundle_id>/`.
   - Emits receipt JSON with bundle metadata + checksum.
   - Removes the original `_apoptosis/<stamp>` directory (optional `--keep-source` flag when rehearsing).

2. `restore` command:
   - Verifies the bundle checksum against `manifest.json`.
   - Extracts the archive into `--dest`.
   - Prints a summary of restored receipts for human verification.

3. Future `verify` subcommand can re-check bundle integrity on CI runners without extracting.

## Receipt schema

`_report/usage/apoptosis/bundles-<ts>.json` entries:

```json
{
  "bundle_id": "apo-20251109T061200Z",
  "created_at": "2025-11-09T06:12:00Z",
  "source_dir": "_apoptosis/2025-11-09/SESSION-123",
  "bundle_path": "artifacts/apoptosis/apo-20251109T061200Z/bundle.tar.xz",
  "bundle_sha256": "…",
  "file_count": 1845,
  "total_bytes": 6231040,
  "receipts": ["_report/usage/prune/receipt-...json"],
  "notes": null
}
```

The CLI appends to `bundles-history.jsonl` so automation can diff prior runs and detect missing bundles.

## CI strategy

1. Guard script checks for tracked files inside `_apoptosis/` matching `*/bundle.tar.xz` (should be absent) and fails when raw directories exceed a configurable count (default 1).
2. During CI, run `python -m tools.autonomy.apoptosis_compress verify --manifest artifacts/apoptosis/<bundle>/manifest.json` to confirm bundle hashes still match.
3. Planner/backlog entries referencing `apoptosis` work must cite the bundle receipt path; `check_plans.py` extension can assert this once bundles ship.

## Rollout steps

1. Land CLI skeleton + manifest helpers (`tools/autonomy/apoptosis_compress.py`).
2. Update hygiene docs (this file + `docs/automation.md`) once CLI is runnable.
3. Backfill existing `_apoptosis/<stamp>` directories into bundles, keeping the last raw snapshot for safety.
4. Enable CI guard after the backfill completes.

This design satisfies plan step **S2** by defining the archive format, metadata schema, CLI interface, and guard/receipt requirements needed for implementation.
