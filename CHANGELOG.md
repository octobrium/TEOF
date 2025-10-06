# Changelog
All notable changes to this project will be documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)  
Versioning: SemVer (0.y until first stable)

---

## [Unreleased]
### Added
- Volatile Data Protocol guard (`scripts/ci/check_vdp.py`) enforces timestamps and sources with fixtures in `datasets/goldens/`.
- Additional VDP fixtures cover future-dated quotes, non-volatile context, and invalid timestamps to exercise guard edges.
- External receipt adapter, keygen, and summary CLIs (`tools/external/adapter.py`, `tools/external/keys.py`, `tools/external/summary.py`) plus signed envelope canon and guard hooks in `scripts/ci/check_vdp.py`.
- Objectives status tooling now tracks L2 O3/O4/O6 signals and conductor receipts
  embed the snapshot for audit trails (`tools/autonomy/objectives_status.py`,
  `tools/autonomy/conductor.py`).
- Relay Insight Sprint collateral kit + dry-run checklist document the pilot
  offer and outreach workflow (`docs/vision/relay-offering-*.md`).
- Authenticity review receipts for the primary truth tier close outstanding
  guardrail tasks (`_report/agent/codex-5/authenticity-review-20250926.md`).
- Impact ledger seeded with instrumentation entry linking automation receipts
  to monetization prep (`docs/vision/impact-ledger.md`, `memory/impact/log.jsonl`).
- Feed keys rotated (`feed.demo-2025`, `feed.sample-2025`) and fresh receipts
  emitted so authenticity trust returns to green (`governance/keys/feed.*.pub`,
  `_report/external/{demo,sample}/20250926*.json`).
- Reflection overview CLI (`teof reflections`) summarises `memory/reflections/` with layer/tag filters and JSON output; docs refreshed with the new anchor.
- TTΔ trend reporting CLI (`teof ttd-trend` / `python -m tools.impact.ttd_trend`) parses `memory/impact/ttd.jsonl`, emits sparklines + readiness alerts, and manager_report now writes the latest summary to `_report/usage/ttd-trend/` with refreshed documentation.

> Tracking work intended for the *next* tag. Use this list instead of a standalone TODO.

### Planned
- **Event staleness filter** (configurable 24h window).
- **Event severity tagging** (`low/medium/high`) + brief synthesis notes.

### Release prep checklist (for next tag)
- [ ] Freeze capsule: update `capsule/vX.Y/hashes.json` and `PROVENANCE.md`.
- [ ] Append anchors event in `governance/anchors.json` (with `prev_content_hash`).
- [ ] Verify CI green on tag and cut GitHub Release (attach `capsule/current/` archive).

---

## [v0.1.0] - 2025-08-22
### Added
- Normalized capsule under `capsule/v1.5` with `capsule/current → v1.5`.
- Canonical docs moved inside capsule and covered by `hashes.json`.
- Single CI workflow (`.github/workflows/teof-ci.yml`) with baseline autodetect, hashes verify, anchors validation, .DS_Store guard, brief smoke test.
- PR Objective-line guard and Minimal v1 workflow.

### Fixed
- Unified brief outputs to `artifacts/ocers_out`; deterministic evaluator stub and fetchers fallback so `make brief` is stable.

### Governance
- `governance/anchors.json` set to `policy: "append-only"`, `immutable_scope` synced to baseline; `releases` entry for `v1.5`.
