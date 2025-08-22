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

## [v0.1.0] - 2025-08-22
### Added
- Normalized capsule under `seed/capsule/v1.5` with `seed/capsule/current → v1.5`.
- Canonical docs moved inside capsule and covered by `hashes.json`.
- Single CI workflow (`.github/workflows/teof-ci.yml`) with baseline autodetect, hashes verify, anchors validation, .DS_Store guard, brief smoke test.
- PR Objective-line guard and Minimal v1 workflow.

### Fixed
- Unified brief outputs to `artifacts/ocers_out`; deterministic evaluator stub and fetchers fallback so `make brief` is stable.

### Governance
- `rings/anchors.json` set to `policy: "append-only"`, `immutable_scope` synced to baseline; `releases` entry for `v1.5`.
