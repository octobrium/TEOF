# Changelog
All notable changes to this project will be documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)  
Versioning: SemVer (0.y until first stable)

---

## [Unreleased]
> Tracking work intended for the *next* tag. Use this list instead of a standalone TODO.

### Planned
- **Evaluator in CI**: enforce OGS/VDP; PRs with uncited volatile data fail.
- **Golden test cases** (`datasets/goldens/`): pass/fail examples for stale/uncited items.
- **Event staleness filter** (configurable 24h window).
- **Event severity tagging** (`low/medium/high`) + brief synthesis notes.

### Release prep checklist (for next tag)
- [ ] Freeze capsule: update `seed/capsule/vX.Y/hashes.json` and `PROVENANCE.md`.
- [ ] Append anchors event in `rings/anchors.json` (with `prev_content_hash`).
- [ ] Verify CI green on tag and cut GitHub Release (attach `seed/capsule/current/` archive).

---

## [v0.1.0] - 2025-08-21  _“First Observer”_
### Added
- **Canonical TEOF core** (axioms, TAP v3.1, VDP/OGS hooks).
- **Freeze-hash flow** via versioned `hashes.json` and provenance.
- **CI integrity checks**:
  - Detect capsule baseline from `seed/capsule/current` or latest `vX.Y`.
  - Verify capsule file digests against baseline `hashes.json`.
  - Validate `rings/anchors.json` schema + append-only events (with `prev_content_hash`).
  - .DS_Store guard.
- **CI smoke test** for brief generation (`make brief`) and artifact presence.

### Changed
- **Repo layout tidy**:
  - Ops scripts → `legacy/ops/`
  - CLI → `branches_thick/cli/`
  - Aperture guideline → `docs/roots/`
- **Single, consolidated workflow** `teof-ci.yml` with clearer logs and baseline materialization.

### Fixed
- `brief` target writes stable artifacts to `artifacts/ocers_out/latest/` for CI checks.

### Security
- Hardened `.gitignore`: `*.egg-info/`, `__pycache__/`, `.venv/`, `artifacts/ocers_out/`.

### Notes
- This release establishes a minimal, auditable core.  
- Provenance for this tag lives at `seed/capsule/v0.1.0/PROVENANCE.md`.
