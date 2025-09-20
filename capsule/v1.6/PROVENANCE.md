# TEOF v1.6 — Provenance

**Date (UTC):** YYYY-MM-DD  
**Branch:** main  
**Tag:** v1.6

## Canonical Artifacts
Digests are recorded in `capsule/v1.6/hashes.json`. Canonical paths:

- `capsule/v1.6/capsule-mini.txt`
- `capsule/v1.6/capsule-handshake.txt`
- `capsule/v1.6/capsule-selfreconstructing.txt`
- `capsule/v1.6/capsule.txt`
- `capsule/v1.6/PROVENANCE.md`
- `capsule/v1.6/RELEASE.md`
- `capsule/v1.6/calibration.md`
- `capsule/v1.6/tests.md`
- `capsule/v1.6/reconstruction.json`

**Note on packaging:** `capsule/current/` is a **materialized directory at release time** (no symlinks) to ensure deterministic builds and CI verification. Attestation files are intentionally excluded, since reproducibility is handled through `hashes.json` and `reconstruction.json`.
