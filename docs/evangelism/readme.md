# Narrative & Evangelism Kit

Status: Active v0.2 (2025-10-03)
Owner: codex-4 (handoff welcomed)
Purpose: equip the operator with ready-to-run stories, assets, and cadence for public outreach.

## How to Use This Kit
1. Pick a story from `docs/evangelism/narrative-arcs.md` that matches the audience.
2. Tailor the one-pager, slide outline, or demo script as needed.
3. Log every external touch under `_report/usage/evangelism/` so guardrails can audit follow through.
4. Sync receipts into the manager report via `python3 -m teof bus_event` when outreach lands.

### Current Assets
- Narrative arcs: `docs/evangelism/narrative-arcs.md` (includes Arc D for capsule cadence)
- One-pager template: `docs/evangelism/one-pager.md`
- Slide deck outline: `docs/evangelism/slide-deck-outline.md`
- Demo video script: `docs/evangelism/demo-video-script.md`
- Distribution cadence: `docs/evangelism/distribution-cadence.md`
- Receipt index: `_report/usage/evangelism/` (cadence + event receipts)

### Evidence Hooks
The kit leans on live receipts to prove trust and automation health:
- Autonomy conductor prompt with authenticity snapshot: `_report/usage/autonomy-conductor/conductor-20250927T195724Z.json`
- Preflight hygiene bundle: `_report/usage/autonomy-preflight/preflight-20250927T200419Z.json`
- Objectives ledger source: `docs/vision/objectives-ledger.md`
- Relay case study scaffold: `docs/impact/relay-insight-case-study.md`
- Capsule cadence summary + anchors: `_report/capsule/summary-latest.json`, `governance/anchors.json`

Keep these receipts updated before sharing assets so external readers can verify claims without private context.
### Logging outreach
Use the CLI helper to capture each touch as a receipt (see `_report/usage/evangelism/` for examples logged 2025-09-29 → 2025-10-03):

```bash
python3 -m tools.receipts.log_event evangelism "Published newsletter" --channel newsletter --arc "Arc B" --asset docs/evangelism/one-pager.md --status published --link https://example.com/post
```

Receipts land under `_report/usage/evangelism/` (see the cadence guide for planned touches).
