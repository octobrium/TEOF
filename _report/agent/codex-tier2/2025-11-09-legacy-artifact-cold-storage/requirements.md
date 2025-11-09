# Legacy Artifact Cold Storage – requirements (2025-11-09)

Backlog reference: `_plans/next-development.todo.json#ND-064`.

Needs:
- Move legacy automation bundles (`_apoptosis/`, `_report/legacy_loop_out/`) into hashed, compressed snapshots to cut repo weight while preserving provenance.
- CLI: `python -m tools.artifacts.cold_storage snapshot --out _report/legacy/snapshots/<ts>.tar.zst --manifest _report/legacy/snapshots/<ts>.json`.
- Must track source receipt hashes + signature, ensure append-only behavior.
- CI guard verifying snapshots exist for artifacts older than threshold; no raw ensembles committed.
- Risks: reproducibility of tarball creation, storage location, verifying chain of custody.
